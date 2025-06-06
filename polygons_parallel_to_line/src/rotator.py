from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.core import QgsPointXY

from .azimuth import calc_delta_azimuth

if TYPE_CHECKING:
    from .line import Line
    from .polygon import Polygon


# TODO: can I use this? https://qgis.org/pyqgis/3.40/core/QgsGeometry.html#qgis.core.QgsGeometry.angleAtVertex
class PolygonRotator:
    def __init__(self, poly: Polygon, closest_line: Line, angle_threshold: float, by_longest: bool):
        self.poly: Polygon = poly
        self.angle_threshold: float = angle_threshold
        self.by_longest: bool = by_longest
        poly_closest_vertex = poly.get_closest_vertex(closest_line)
        self.prev_poly_segment, self.next_poly_segment = poly.get_adjacent_segments(poly_closest_vertex)
        line_segment = closest_line.get_closest_segment(QgsPointXY(poly_closest_vertex))
        self.prev_delta_azimuth: float = calc_delta_azimuth(line_segment.azimuth, self.prev_poly_segment.azimuth)
        self.next_delta_azimuth: float = calc_delta_azimuth(line_segment.azimuth, self.next_poly_segment.azimuth)

    def rotate(self) -> None:
        if abs(self.prev_delta_azimuth) <= self.angle_threshold >= abs(self.next_delta_azimuth):
            if self.by_longest:
                return self.rotate_by_longest_segment()
            return self.rotate_by_smallest_angle()

        for delta_azimuth in (self.prev_delta_azimuth, self.next_delta_azimuth):
            if abs(delta_azimuth) <= self.angle_threshold:
                return self.rotate_by_angle(delta_azimuth)

    def rotate_by_angle(self, angle: float) -> None:
        self.poly.rotate(angle)

    def rotate_by_longest_segment(self) -> None:
        """Rotates the polygon based on the longest segment. If segments are equal length, falls back to rotating by
        the smallest angle.
        """
        if self.prev_poly_segment.length > self.next_poly_segment.length:
            self.rotate_by_angle(self.prev_delta_azimuth)
        elif self.prev_poly_segment.length < self.next_poly_segment.length:
            self.rotate_by_angle(self.next_delta_azimuth)
        else:
            self.rotate_by_smallest_angle()

    def rotate_by_smallest_angle(self) -> None:
        """Rotates the polygon by the angle with the smallest absolute value."""
        if abs(self.prev_delta_azimuth) > abs(self.next_delta_azimuth):
            self.rotate_by_angle(self.next_delta_azimuth)
        else:
            self.rotate_by_angle(self.prev_delta_azimuth)
