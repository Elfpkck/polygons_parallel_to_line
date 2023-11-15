from __future__ import annotations

import enum
import os
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsFeatureSink, QgsField, QgsGeometry, QgsPoint, QgsProcessingException, QgsSpatialIndex
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from qgis.core import QgsProcessingAlgorithm


import pydevd_pycharm


class Cfg(str, enum.Enum):
    OUTPUT_LAYER = "OUTPUT_LAYER"
    LINE_LAYER = "LINE_LAYER"
    POLYGON_LAYER = "POLYGON_LAYER"
    SELECTED = "SELECTED"
    WRITE_SELECTED = "WRITE_SELECTED"
    LONGEST = "LONGEST"
    MULTI = "MULTI"
    DISTANCE = "DISTANCE"
    ANGLE = "ANGLE"
    COLUMN_NAME = "_rotated"


class PolygonsParallelToLine:
    def __init__(self, algo: QgsProcessingAlgorithm, parameters, context, feedback):
        self.algo = algo
        self.parameters = parameters
        self.context = context
        self.feedback = feedback

    def run(self) -> dict[str, Any]:
        # pydevd_pycharm.settrace("127.0.0.1", port=53100, stdoutToServer=True, stderrToServer=True)
        self.operation_counter = 0
        # self._progress = progress
        self.get_input_values()

        self.create_line_spatial_index()
        self.validate_polygon_layer()
        self.add_attribute()
        self.lines_dict = {x.id(): x for x in self.line_layer.getFeatures()}
        self.rotate_and_write_selected_or_all()
        self.delete_attribute()
        ret = {Cfg.OUTPUT_LAYER: self.dest_id}
        if os.getenv("PPTL_TEST"):
            output_layer = self.context.getMapLayer(self.dest_id)
            line = [x.geometry() for x in self.line_layer.getFeatures()][0].asWkt()  # TODO: remove
            poly = [x.geometry() for x in self.polygon_layer.getFeatures()][0].asWkt()  # TODO: remove
            ret["result"] = [x.geometry() for x in output_layer.getFeatures()][0].asWkt()
        return ret

    def get_input_values(self):
        parameters, context = self.parameters, self.context
        self.line_layer = self.algo.parameterAsVectorLayer(parameters, Cfg.LINE_LAYER, context)
        self.polygon_layer = self.algo.parameterAsVectorLayer(parameters, Cfg.POLYGON_LAYER, context)
        self.is_selected = self.algo.parameterAsBool(
            parameters, Cfg.SELECTED, context
        )  # TODO use "Selected features only" checkbox instead
        self.is_write_selected = self.algo.parameterAsBool(parameters, Cfg.WRITE_SELECTED, context)
        self.by_longest = self.algo.parameterAsBool(parameters, Cfg.LONGEST, context)
        self.multi = self.algo.parameterAsBool(parameters, Cfg.MULTI, context)
        self.distance = self.algo.parameterAsInt(parameters, Cfg.DISTANCE, context)
        self.angle = self.algo.parameterAsInt(parameters, Cfg.ANGLE, context)
        (self.sink, self.dest_id) = self.algo.parameterAsSink(
            parameters,
            Cfg.OUTPUT_LAYER,
            context,
            self.polygon_layer.fields(),
            self.polygon_layer.wkbType(),
            self.polygon_layer.sourceCrs(),
        )

    def create_line_spatial_index(self):
        spatial_index = QgsSpatialIndex()
        spatial_index.addFeatures(self.line_layer.getFeatures())
        self.index = spatial_index

    def validate_polygon_layer(self):
        self.total_number = self.polygon_layer.featureCount()
        if not self.total_number:
            raise QgsProcessingException(self.algo.tr("Layer does not have any polygons"))
        if self.is_write_selected and not self.is_selected:
            raise QgsProcessingException(
                self.algo.tr('You have chosen "Save only selected" without ' '"Rotate only selected polygons"')
            )
        if self.is_selected:
            self.total_number = self.polygon_layer.selectedFeatureCount()
            if not self.total_number:
                raise QgsProcessingException(
                    self.algo.tr('You have chosen "Rotate only selected polygons" ' "but there are no selected")
                )

    def add_attribute(self):
        for attr in self.polygon_layer.fields():
            if Cfg.COLUMN_NAME == attr.name():
                if attr.isNumeric():
                    break

                self.delete_attribute()
        else:
            self.polygon_layer.dataProvider().addAttributes([QgsField(Cfg.COLUMN_NAME, QVariant.Int)])
            self.polygon_layer.updateFields()

    def delete_attribute(self):
        for i, attr in enumerate(self.polygon_layer.fields()):
            if attr.name() == Cfg.COLUMN_NAME:
                self.polygon_layer.dataProvider().deleteAttributes([i])
                self.polygon_layer.updateFields()

    def rotate_and_write_selected_or_all(self):
        if self.is_selected:
            self.rotate_and_write_selected()
        else:
            for polygon in self.polygon_layer.getFeatures():
                self.rotate_and_write_polygon(polygon)

    def rotate_and_write_selected(self):
        if self.is_write_selected:
            for polygon in self.polygon_layer.selectedFeatures():
                self.rotate_and_write_polygon(polygon)
        else:
            selected_polygons_ids = self.polygon_layer.selectedFeaturesIds()
            for p in self.polygon_layer.getFeatures():
                if p.id() in selected_polygons_ids:
                    self.rotate_and_write_polygon(p)
                else:
                    self.sink.addFeature(p, QgsFeatureSink.FastInsert)  # TODO: addFeatures

    def rotate_and_write_polygon(self, polygon):
        self.progress_bar()
        self.p = polygon
        self.initiate_rotation()
        self.sink.addFeature(self.p, QgsFeatureSink.FastInsert)  # TODO: addFeatures

    def progress_bar(self):
        self.operation_counter += 1
        current_percentage = self.operation_counter / self.total_number * 100
        # self._progress.setPercentage(round(current_percentage))

    def initiate_rotation(self):
        self.get_nearest_line()
        dist = self.nearest_line.geometry().distance(self.p.geometry())
        if not self.distance or dist <= self.distance:
            self.simple_or_multi_geometry()

    def get_nearest_line(self):
        self.center = self.p.geometry().centroid().asPoint()
        near_id = self.index.nearestNeighbor(self.center, 1)
        self.nearest_line = self.lines_dict.get(near_id[0])

    def simple_or_multi_geometry(self):
        is_multi = self.p.geometry().isMultipart()
        if is_multi and not self.multi:
            dct = {}
            m_polygon_vertexes = self.p.geometry().asMultiPolygon()
            for i, part in enumerate(m_polygon_vertexes):
                min_distance, vertex_index = self.get_nearest_vertex(part[0][:-1])
                dct[(i, vertex_index)] = min_distance
            i, vertex_index = min(dct, key=dct.get)
            self.nearest_edges(m_polygon_vertexes[i][0][:-1], vertex_index)
        elif not is_multi:
            polygon_vertexes = self.p.geometry().asPolygon()[0][:-1]
            _, vertex_index = self.get_nearest_vertex(polygon_vertexes)
            self.nearest_edges(polygon_vertexes, vertex_index)

    def get_nearest_vertex(self, polygon_vertexes):
        vertex_to_segment_dict = {}
        for vertex in polygon_vertexes:
            vertex_geom = QgsGeometry.fromPointXY(vertex)
            vertex_to_segment = vertex_geom.distance(self.nearest_line.geometry())  # float as key? TODO: change?
            vertex_to_segment_dict[vertex_to_segment] = vertex

        min_distance = min(vertex_to_segment_dict.keys())
        self.nearest_vertex = vertex_to_segment_dict[min_distance]
        vertex_index = polygon_vertexes.index(self.nearest_vertex)
        return min_distance, vertex_index

    def nearest_edges(self, polygon_vertexes, vertex_index):
        if vertex_index == 0:  # if vertex is first
            self.line1 = QgsGeometry.fromPolyline([QgsPoint(polygon_vertexes[0]), QgsPoint(polygon_vertexes[1])])
            self.line2 = QgsGeometry.fromPolyline([QgsPoint(polygon_vertexes[0]), QgsPoint(polygon_vertexes[-1])])
        elif vertex_index == len(polygon_vertexes) - 1:  # if vertex is last
            self.line1 = QgsGeometry.fromPolyline([QgsPoint(polygon_vertexes[-1]), QgsPoint(polygon_vertexes[0])])
            self.line2 = QgsGeometry.fromPolyline([QgsPoint(polygon_vertexes[-1]), QgsPoint(polygon_vertexes[-2])])
        else:
            self.line1 = QgsGeometry.fromPolyline(
                [QgsPoint(polygon_vertexes[vertex_index]), QgsPoint(polygon_vertexes[vertex_index + 1])]
            )
            self.line2 = QgsGeometry.fromPolyline(
                [QgsPoint(polygon_vertexes[vertex_index]), QgsPoint(polygon_vertexes[vertex_index - 1])]
            )
        # azimuth() returns 0-180 and 0-(-180) values. 0 - north, 90 - east, 180 - south, -90 - west
        line1_azimuth = self.line1.asPolyline()[0].azimuth(self.line1.asPolyline()[1])
        line2_azimuth = self.line2.asPolyline()[0].azimuth(self.line2.asPolyline()[1])
        # this 2 azimuth FROM the closest vertex TO the next and previous vertexes
        self.segment_azimuth(line1_azimuth, line2_azimuth)

    def segment_azimuth(self, line1_azimuth, line2_azimuth):
        nearest_line_geom = self.nearest_line.geometry()
        if nearest_line_geom.isMultipart():
            dct = {}
            min_dists = set()

            for line in nearest_line_geom.asMultiPolyline():
                l = QgsGeometry.fromPolyline([QgsPoint(x) for x in line])
                min_dist, _, greater_vertex_index, _ = l.closestSegmentWithContext(self.nearest_vertex)
                min_dists.add(min_dist)
                dct[min_dist] = [line, greater_vertex_index]

            min_distance = min(min_dists)
            line_ = dct[min_distance][0]
            index_segm_end = dct[min_distance][1]
            segm_end = line_[index_segm_end]
            segm_start = line_[index_segm_end - 1]
        else:
            min_dist, _, greater_vertex_index, _ = nearest_line_geom.closestSegmentWithContext(self.nearest_vertex)
            segm_end = nearest_line_geom.asPolyline()[greater_vertex_index]
            segm_start = nearest_line_geom.asPolyline()[greater_vertex_index - 1]

        segment_azimuth = segm_start.azimuth(segm_end)  # this azimuth can be x or (180 - x)
        dlt_az1 = self.get_delta_azimuth(segment_azimuth, line1_azimuth)
        dlt_az2 = self.get_delta_azimuth(segment_azimuth, line2_azimuth)

        self.rotate(dlt_az1, dlt_az2)

    @staticmethod
    def make_azimuth_positive(azimuth):
        """Make azimuth positive (same semicircle directions)"""
        if azimuth == -180:
            azimuth = 180
        elif azimuth < 0:
            azimuth += 180
        return azimuth

    def get_delta_azimuth(self, segment_azimuth, line_azimuth):
        segment_azimuth = self.make_azimuth_positive(segment_azimuth)
        line_azimuth = self.make_azimuth_positive(line_azimuth)
        delta_azimuth = segment_azimuth - line_azimuth

        # make abs(delta azimuth) < 90
        if delta_azimuth > 90:  # TODO: check 90
            delta_azimuth -= 180
        elif delta_azimuth < -90:
            delta_azimuth += 180
        return delta_azimuth

    def rotate(self, delta1, delta2):
        self.rotation_check = True
        if abs(delta1) <= self.angle >= abs(delta2):
            if self.by_longest:
                self.rotate_by_longest(delta1, delta2)
            else:
                self.rotate_not_by_longest(delta1, delta2)
        else:
            self.others_rotations(delta1, delta2)

        self.mark_as_rotated()

    def rotate_by_longest(self, delta1, delta2):
        length1 = self.line1.length()
        length2 = self.line2.length()

        if length1 > length2:
            geom = self.p.geometry()
            # rotate() takes any positive and negative values. positive - clockwise, negative - counterclockwise
            geom.rotate(delta1, self.center)
            self.p.setGeometry(geom)
        elif length1 < length2:
            geom = self.p.geometry()
            geom.rotate(delta2, self.center)
            self.p.setGeometry(geom)
        elif length1 == length2:
            self.rotate_not_by_longest(delta1, delta2)
        else:  # TODO: unreachable
            self.rotation_check = False

    def rotate_not_by_longest(self, delta1, delta2):
        if abs(delta1) > abs(delta2):
            geom = self.p.geometry()
            geom.rotate(delta2, self.center)
            self.p.setGeometry(geom)
        elif abs(delta1) <= abs(delta2):
            geom = self.p.geometry()
            geom.rotate(delta1, self.center)
            self.p.setGeometry(geom)
        else:
            self.rotation_check = False

    def others_rotations(self, delta1, delta2):
        if abs(delta1) <= self.angle:
            geom = self.p.geometry()
            geom.rotate(delta1, self.center)
            self.p.setGeometry(geom)
        elif abs(delta2) <= self.angle:
            geom = self.p.geometry()
            self.p.geometry().rotate(delta2, self.center)
            self.p.setGeometry(geom)
        else:
            self.rotation_check = False

    def mark_as_rotated(self):
        if self.rotation_check:
            self.p[Cfg.COLUMN_NAME] = 1


# TODO: for the future: a method to make 2 objects (lines, polygons) parallel
# TODO: update translations including path
