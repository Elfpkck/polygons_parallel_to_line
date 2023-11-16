from __future__ import annotations

from qgis.core import QgsFeature, QgsGeometry, QgsPoint
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    pass


class Rotator:
    def __init__(self, polygon, lines_dict, index, new_fields, by_longest, no_multi, distance, angle):
        self.p = polygon
        self.lines_dict = lines_dict
        self.index = index
        self.new_fields = new_fields
        self.by_longest = by_longest
        self.no_multi = no_multi
        self.distance = distance
        self.angle = angle
        self.rotation_check = False

    def get_rotated_polygon(self):
        polygon = self.p
        self.initiate_rotation()

        new_feature = QgsFeature(self.new_fields)
        new_feature.setGeometry(polygon.geometry())
        attrs = polygon.attributes()
        if self.rotation_check:
            attrs.append(1)
        new_feature.setAttributes(attrs)
        return new_feature

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
        if is_multi and not self.no_multi:
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
        if abs(delta1) <= self.angle >= abs(delta2):
            if self.by_longest:
                self.rotate_by_longest(delta1, delta2)
            else:
                self.rotate_not_by_longest(delta1, delta2)
        else:
            self.others_rotations(delta1, delta2)

    def _rotate(self, angle: float):
        """QgsGeometry.rotate() takes any positive and negative values. Positive - rotate clockwise,
        negative - counterclockwise.
        """
        geom = self.p.geometry()
        geom.rotate(angle, self.center)
        self.p.setGeometry(geom)
        self.rotation_check = True

    def rotate_by_longest(self, delta1, delta2):
        length1 = self.line1.length()
        length2 = self.line2.length()

        if length1 > length2:
            self._rotate(delta1)
        elif length1 < length2:
            self._rotate(delta2)
        else:
            self.rotate_not_by_longest(delta1, delta2)

    def rotate_not_by_longest(self, delta1, delta2):
        self._rotate(delta2) if delta1 > delta2 else self._rotate(delta1)

    def others_rotations(self, delta1, delta2):
        if abs(delta1) <= self.angle:
            self._rotate(delta1)
        elif abs(delta2) <= self.angle:
            self._rotate(delta2)
