from __future__ import annotations

from qgis.core import QgsGeometry, QgsPoint
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .polygon import Polygon


class Rotator:
    def __init__(self):
        self.rotation_check = False

    @staticmethod
    def get_line_azimuth(line) -> int:
        """azimuth() returns 0-180 and 0-(-180) values. 0 - north, 90 - east, 180 - south, -90 - west"""
        as_polyline = line.asPolyline()
        assert len(as_polyline) == 2, f"Line must have 2 vertexes but has {len(as_polyline)}"
        return as_polyline[0].azimuth(as_polyline[1])

    # TODO: move parts to new Line class?
    @staticmethod
    def get_line_segment_azimuth(nearest_line_geom, nearest_vertex):
        if nearest_line_geom.isMultipart():
            dct = {}
            min_dists = set()

            for line in nearest_line_geom.asMultiPolyline():
                l = QgsGeometry.fromPolyline([QgsPoint(x) for x in line])
                min_dist, _, greater_vertex_index, _ = l.closestSegmentWithContext(nearest_vertex)
                min_dists.add(min_dist)
                dct[min_dist] = [line, greater_vertex_index]

            min_distance = min(min_dists)
            line_ = dct[min_distance][0]
            index_segm_end = dct[min_distance][1]
            segm_end = line_[index_segm_end]
            segm_start = line_[index_segm_end - 1]
        else:
            min_dist, _, greater_vertex_index, _ = nearest_line_geom.closestSegmentWithContext(nearest_vertex)
            segm_end = nearest_line_geom.asPolyline()[greater_vertex_index]
            segm_start = nearest_line_geom.asPolyline()[greater_vertex_index - 1]

        return segm_start.azimuth(segm_end)  # this azimuth can be x or (180 - x)

    @staticmethod
    def as_positive_azimuth(azimuth):
        """Make azimuth positive (same semicircle directions)"""
        if azimuth == -180:
            azimuth = 180
        elif azimuth < 0:
            azimuth += 180
        return azimuth

    def get_delta_azimuth(self, segment_azimuth, line_azimuth):
        segment_azimuth = self.as_positive_azimuth(segment_azimuth)
        line_azimuth = self.as_positive_azimuth(line_azimuth)
        delta_azimuth = segment_azimuth - line_azimuth

        # make abs(delta azimuth) < 90
        if delta_azimuth > 90:  # TODO: check 90
            delta_azimuth -= 180
        elif delta_azimuth < -90:
            delta_azimuth += 180
        return delta_azimuth

    def _rotate(self, angle: float, poly: Polygon):
        """QgsGeometry.rotate() takes any positive and negative values. Positive - rotate clockwise,
        negative - counterclockwise.
        """
        poly.geom.rotate(angle, poly.center)
        poly.poly.setGeometry(poly.geom)
        self.rotation_check = True

    def rotate_by_longest(self, delta1, delta2, length1, length2, poly: Polygon):
        if length1 > length2:
            self._rotate(delta1, poly)
        elif length1 < length2:
            self._rotate(delta2, poly)
        else:
            self.rotate_not_by_longest(delta1, delta2, poly)

    def rotate_not_by_longest(self, delta1, delta2, poly):
        self._rotate(delta2, poly) if delta1 > delta2 else self._rotate(delta1, poly)

    def others_rotations(self, delta1, delta2, poly, angle):
        if abs(delta1) <= angle:
            self._rotate(delta1, poly)
        elif abs(delta2) <= angle:
            self._rotate(delta2, poly)
