from __future__ import annotations

from typing import TYPE_CHECKING

from .azimuth import calc_delta_azimuth

if TYPE_CHECKING:
    from .line import Line
    from .polygon import Polygon


class PolygonRotator:
    def __init__(self, poly: Polygon, closest_line: Line, angle_threshold: float, by_longest: bool):
        self.poly = poly
        self.angle_threshold = angle_threshold
        self.by_longest = by_longest

        closest_poly_part = poly.get_closest_single_poly(closest_line.geom)
        self.edge_1, self.edge_2 = closest_poly_part.closest_edges_pair
        # Azimuths from the closest vertex pointing to adjacent vertices (next and previous)
        edge_1_azimuth, edge_2_azimuth = self.edge_1.get_line_azimuth(), self.edge_2.get_line_azimuth()
        line_segment_azimuth = closest_line.get_closest_segment_azimuth(closest_poly_part.closest_vertex)
        self.delta1 = calc_delta_azimuth(line_segment_azimuth, edge_1_azimuth)
        self.delta2 = calc_delta_azimuth(line_segment_azimuth, edge_2_azimuth)

    def rotate(self) -> None:
        if abs(self.delta1) <= self.angle_threshold and abs(self.delta2) <= self.angle_threshold:
            if self.by_longest:
                return self.rotate_by_longest_edge()
            return self.rotate_by_smallest_angle()

        for delta in (self.delta1, self.delta2):
            if abs(delta) <= self.angle_threshold:
                return self.rotate_by_angle(delta)

    def rotate_by_angle(self, angle: float) -> None:
        """QgsGeometry.rotate() takes any positive and negative values. Positive - rotate clockwise,
        negative - counterclockwise.
        """
        self.poly.geom.rotate(angle, self.poly.center)
        self.poly.poly.setGeometry(self.poly.geom)
        self.poly.is_rotated = True

    def rotate_by_longest_edge(self) -> None:
        """Rotates the polygon based on the longest edge. If edges are equal length, falls back to rotating by
        the smallest angle.
        """
        length1, length2 = self.edge_1.length, self.edge_2.length
        if length1 > length2:
            self.rotate_by_angle(self.delta1)
        elif length1 < length2:
            self.rotate_by_angle(self.delta2)
        else:
            self.rotate_by_smallest_angle()

    def rotate_by_smallest_angle(self) -> None:
        """Rotates the polygon by the angle with the smallest absolute value."""
        angle = self.delta2 if abs(self.delta1) > abs(self.delta2) else self.delta1
        self.rotate_by_angle(angle)
