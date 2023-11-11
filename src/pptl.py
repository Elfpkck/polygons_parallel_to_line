from __future__ import annotations

import enum
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
        self._operation_counter = 0
        # self._progress = progress
        self._get_input_values()

        self._create_line_spatial_index()
        self._validate_polygon_layer()
        self._add_attribute()
        self._lines_dict = {x.id(): x for x in self._line_layer.getFeatures()}
        self._rotate_and_write_selected_or_all()
        self._delete_attribute()
        vlyr = self.context.getMapLayer(self.dest_id)  # TODO: for testing only
        line = [x.geometry() for x in self._line_layer.getFeatures()][0].asWkt()
        poly = [x.geometry() for x in self._polygon_layer.getFeatures()][0].asWkt()
        result = [x.geometry() for x in vlyr.getFeatures()][0].asWkt()
        return {Cfg.OUTPUT_LAYER: self.dest_id, "result": result}

    def _get_input_values(self):
        parameters, context = self.parameters, self.context
        self._line_layer = self.algo.parameterAsVectorLayer(parameters, Cfg.LINE_LAYER, context)
        self._polygon_layer = self.algo.parameterAsVectorLayer(parameters, Cfg.POLYGON_LAYER, context)
        self._is_selected = self.algo.parameterAsBool(
            parameters, Cfg.SELECTED, context
        )  # TODO use "Selected features only" checkbox instead
        self._is_write_selected = self.algo.parameterAsBool(parameters, Cfg.WRITE_SELECTED, context)
        self._by_longest = self.algo.parameterAsBool(parameters, Cfg.LONGEST, context)
        self._multi = self.algo.parameterAsBool(parameters, Cfg.MULTI, context)
        self._distance = self.algo.parameterAsInt(parameters, Cfg.DISTANCE, context)
        self._angle = self.algo.parameterAsInt(parameters, Cfg.ANGLE, context)
        (self.sink, self.dest_id) = self.algo.parameterAsSink(
            parameters,
            Cfg.OUTPUT_LAYER,
            context,
            self._polygon_layer.fields(),
            self._polygon_layer.wkbType(),
            self._polygon_layer.sourceCrs(),
        )

    def _create_line_spatial_index(self):
        self._index = QgsSpatialIndex()
        for line in self._line_layer.getFeatures():
            self._index.insertFeature(line)

    def _validate_polygon_layer(self):
        self._totalNumber = self._polygon_layer.featureCount()
        if not self._totalNumber:
            raise QgsProcessingException(self.algo.tr("Layer does not have any polygons"))
        if self._is_write_selected and not self._is_selected:
            raise QgsProcessingException(
                self.algo.tr('You have chosen "Save only selected" without ' '"Rotate only selected polygons"')
            )
        if self._is_selected:
            self._totalNumber = self._polygon_layer.selectedFeatureCount()
            if not self._totalNumber:
                raise QgsProcessingException(
                    self.algo.tr('You have chosen "Rotate only selected polygons" ' "but there are no selected")
                )

    def _add_attribute(self):
        for attr in self._polygon_layer.fields():
            if Cfg.COLUMN_NAME == attr.name():
                if attr.isNumeric():
                    break
                else:
                    self._delete_attribute()
        else:
            self._polygon_layer.dataProvider().addAttributes([QgsField(Cfg.COLUMN_NAME, QVariant.Int)])
            self._polygon_layer.updateFields()

    def _delete_attribute(self):
        for i, attr in enumerate(self._polygon_layer.fields()):
            if attr.name() == Cfg.COLUMN_NAME:
                self._polygon_layer.dataProvider().deleteAttributes([i])
                self._polygon_layer.updateFields()

    def _rotate_and_write_selected_or_all(self):
        if self._is_selected:
            self._rotate_and_write_seleced()
        else:
            polygons = self._polygon_layer.getFeatures()
            for polygon in polygons:
                self._rotate_and_write_polygon(polygon)

    def _rotate_and_write_seleced(self):
        if self._is_write_selected:
            for polygon in self._polygon_layer.selectedFeatures():
                self._rotate_and_write_polygon(polygon)
        else:
            selectedPolygonsIds = self._polygon_layer.selectedFeaturesIds()
            for p in self._polygon_layer.getFeatures():
                if p.id() in selectedPolygonsIds:
                    self._rotate_and_write_polygon(p)
                else:
                    self.sink.addFeature(p, QgsFeatureSink.FastInsert)  # TODO: addFeatures

    def _rotate_and_write_polygon(self, polygon):
        self._progress_bar()
        self._p = polygon
        self._initiate_rotation()
        self.sink.addFeature(self._p, QgsFeatureSink.FastInsert)  # TODO: addFeatures

    def _progress_bar(self):
        self._operation_counter += 1
        currentPercentage = self._operation_counter / self._totalNumber * 100
        # self._progress.setPercentage(round(currentPercentage))

    def _initiate_rotation(self):
        self._get_nearest_line()
        dist = self._nearLine.geometry().distance(self._p.geometry())
        if not self._distance or dist <= self._distance:
            self._simple_or_multi_geometry()

    def _get_nearest_line(self):
        self._center = self._p.geometry().centroid()
        nearId = self._index.nearestNeighbor(self._center.asPoint(), 1)
        self._nearLine = self._lines_dict.get(nearId[0])

    def _simple_or_multi_geometry(self):
        isMulti = self._p.geometry().isMultipart()
        if isMulti and not self._multi:
            dct = {}
            mPolygonVertexes = self._p.geometry().asMultiPolygon()
            for i, part in enumerate(mPolygonVertexes):
                minDistance, vertexIndex = self._get_nearest_vertex(part[0])
                dct[(i, vertexIndex)] = minDistance
            i, vertexIndex = min(dct, key=dct.get)
            self._nearest_edges(mPolygonVertexes[i][0], vertexIndex)
        elif not isMulti:
            polygonVertexes = self._p.geometry().asPolygon()[0][:-1]
            vertexIndex = self._get_nearest_vertex(polygonVertexes)[1]
            self._nearest_edges(polygonVertexes, vertexIndex)

    def _get_nearest_vertex(self, polygonVertexes):
        vertexToSegmentDict = {}
        for vertex in polygonVertexes:
            vertexGeom = QgsGeometry.fromPointXY(vertex)
            vertexToSegment = vertexGeom.distance(self._nearLine.geometry())
            vertexToSegmentDict[vertexToSegment] = vertex

        minDistance = min(vertexToSegmentDict.keys())
        self._nearestVertex = vertexToSegmentDict[minDistance]
        vertexIndex = polygonVertexes.index(self._nearestVertex)
        return minDistance, vertexIndex

    def _nearest_edges(self, polygonVertexes, vertexIndex):
        # if vertex is first
        if vertexIndex == 0:
            self._line1 = QgsGeometry.fromPolyline([QgsPoint(polygonVertexes[0]), QgsPoint(polygonVertexes[1])])
            self._line2 = QgsGeometry.fromPolyline([QgsPoint(polygonVertexes[0]), QgsPoint(polygonVertexes[-1])])

        # if vertex is last
        elif vertexIndex == len(polygonVertexes) - 1:
            self._line1 = QgsGeometry.fromPolyline([QgsPoint(polygonVertexes[-1]), QgsPoint(polygonVertexes[0])])
            self._line2 = QgsGeometry.fromPolyline([QgsPoint(polygonVertexes[-1]), QgsPoint(polygonVertexes[-2])])
        else:
            self._line1 = QgsGeometry.fromPolyline(
                [QgsPoint(polygonVertexes[vertexIndex]), QgsPoint(polygonVertexes[vertexIndex + 1])]
            )
            self._line2 = QgsGeometry.fromPolyline(
                [QgsPoint(polygonVertexes[vertexIndex]), QgsPoint(polygonVertexes[vertexIndex - 1])]
            )

        line1Azimuth = self._line1.asPolyline()[0].azimuth(self._line1.asPolyline()[1])
        line2Azimuth = self._line2.asPolyline()[0].azimuth(self._line2.asPolyline()[1])
        self._segment_azimuth(line1Azimuth, line2Azimuth)

    def _segment_azimuth(self, line1Azimuth, line2Azimuth):
        nearLineGeom = self._nearLine.geometry()
        if nearLineGeom.isMultipart():
            dct = {}
            minDists = []

            for line in nearLineGeom.asMultiPolyline():
                l = QgsGeometry.fromPolyline([QgsPoint(x) for x in line])
                closestSegmContext = l.closestSegmentWithContext(self._nearestVertex)
                minDists.append(closestSegmContext[0])
                dct[closestSegmContext[0]] = [line, closestSegmContext[-1]]

            minDistance = min(minDists)
            closestSegment = dct[minDistance][0]
            indexSegmEnd = dct[minDistance][1]
            segmEnd = closestSegment[indexSegmEnd]
            segmStart = closestSegment[indexSegmEnd - 1]
        else:
            closestSegmContext = nearLineGeom.closestSegmentWithContext(self._nearestVertex)
            indexSegmEnd = closestSegmContext[-1]
            segmEnd = nearLineGeom.asPolyline()[indexSegmEnd]
            segmStart = nearLineGeom.asPolyline()[indexSegmEnd - 1]

        segmentAzimuth = segmStart.azimuth(segmEnd)
        self._dltAz1 = self._get_delta_azimuth(segmentAzimuth, line1Azimuth)
        self._dltAz2 = self._get_delta_azimuth(segmentAzimuth, line2Azimuth)

        self._azimuth()

    def _get_delta_azimuth(self, segment, line):
        if (segment >= 0 and line >= 0) or (segment <= 0 and line <= 0):
            delta = segment - line
            if segment > line and abs(delta) > 90:
                delta -= 180
            elif segment < line and abs(delta) > 90:
                delta += 180

        if 90 >= segment >= 0 and line <= 0:
            delta = segment + abs(line)
            if delta > 90:
                delta -= 180
        elif 90 < segment and line <= 0:
            delta = segment - line - 180
            if abs(delta) > 90:
                delta -= 180

        if -90 <= segment <= 0 and line >= 0:
            delta = segment - line
            if abs(delta) > 90:
                delta += 180
        elif -90 > segment and line >= 0:
            delta = segment - line + 180
            if abs(delta) > 90:
                delta += 180

        return delta

    def _azimuth(self):
        delta1 = abs(self._dltAz1)
        delta2 = abs(self._dltAz2)

        if abs(self._dltAz1) > 90:
            delta1 = 180 - delta1
        if abs(self._dltAz2) > 90:
            delta2 = 180 - delta2

        self._rotate(delta1, delta2)

    def _rotate(self, delta1, delta2):
        self._rotationCheck = True
        if delta1 <= self._angle and delta2 <= self._angle:
            if self._by_longest:
                self._rotate_by_longest(delta1, delta2)
            else:
                self._rotate_not_by_longest(delta1, delta2)
        else:
            self._others_rotations(delta1, delta2)

        self._mark_as_rotated()

    def _rotate_by_longest(self, delta1, delta2):
        if delta1 <= self._angle and delta2 <= self._angle:
            length1 = self._line1.length()
            length2 = self._line2.length()

            if length1 >= length2:
                geom = self._p.geometry()
                geom.rotate(self._dltAz1, self._center.asPoint())
                self._p.setGeometry(geom)
            elif length1 < length2:
                geom = self._p.geometry()
                geom.rotate(self._dltAz2, self._center.asPoint())
                self._p.setGeometry(geom)
            elif length1 == length2:
                self._rotate_not_by_longest(delta1, delta2)
            else:
                self._rotationCheck = False

    def _rotate_not_by_longest(self, delta1, delta2):
        if delta1 > delta2:
            geom = self._p.geometry()
            geom.rotate(self._dltAz2, self._center.asPoint())
            self._p.setGeometry(geom)
        elif delta1 <= delta2:
            geom = self._p.geometry()
            geom.rotate(self._dltAz1, self._center.asPoint())
            self._p.setGeometry(geom)
        else:
            self._rotationCheck = False

    def _others_rotations(self, delta1, delta2):
        if delta1 <= self._angle:
            geom = self._p.geometry()
            geom.rotate(self._dltAz1, self._center.asPoint())
            self._p.setGeometry(geom)
        elif delta2 <= self._angle:
            geom = self._p.geometry()
            self._p.geometry().rotate(self._dltAz2, self._center.asPoint())
            self._p.setGeometry(geom)
        else:
            self._rotationCheck = False

    def _mark_as_rotated(self):
        if self._rotationCheck:
            self._p[Cfg.COLUMN_NAME] = 1


# TODO: for the future: a method to make 2 objects (lines, polygons) parallel
# TODO: update translations including path
