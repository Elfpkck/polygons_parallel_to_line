from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .polygon import Polygon


class PolygonRotator:
    def __init__(self, poly: Polygon, delta1: float, delta2: float):
        self.poly = poly
        self.delta1 = delta1
        self.delta2 = delta2

    def rotate(self, edge1_len: float, edge2_len: float, angle_threshold: float, by_longest: bool) -> None:
        if abs(self.delta1) <= angle_threshold and abs(self.delta2) <= angle_threshold:
            if by_longest:
                return self.rotate_by_longest_edge(edge1_len, edge2_len)
            return self.rotate_by_smallest_angle()

        for delta in (self.delta1, self.delta2):
            if abs(delta) <= angle_threshold:
                return self.rotate_by_angle(delta)

    def rotate_by_angle(self, angle: float) -> None:
        """QgsGeometry.rotate() takes any positive and negative values. Positive - rotate clockwise,
        negative - counterclockwise.
        """
        self.poly.geom.rotate(angle, self.poly.center)
        self.poly.poly.setGeometry(self.poly.geom)
        self.poly.is_rotated = True

    def rotate_by_longest_edge(self, length1: float, length2: float) -> None:
        """Rotates the polygon based on the longest edge. If edges are equal length, falls back to rotating by
        the smallest angle.
        """
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
