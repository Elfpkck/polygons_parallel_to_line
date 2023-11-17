from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .polygon import Polygon


class Rotator:
    def __init__(self):
        self.rotation_check = False

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
