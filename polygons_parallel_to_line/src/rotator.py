from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .polygon import Polygon


class DeltaAzimuth:
    def __init__(self, segment_azimuth, line_azimuth):
        self.segment_azimuth = segment_azimuth
        self.line_azimuth = line_azimuth
        delta_azimuth = self.as_positive_azimuth(segment_azimuth) - self.as_positive_azimuth(line_azimuth)
        self.delta_azimuth = self.as_less_than_90_azimuth(delta_azimuth)

    @staticmethod
    def as_positive_azimuth(azimuth):
        """Make azimuth positive (same semicircle directions)."""
        if azimuth == -180:
            azimuth = 180
        elif azimuth < 0:
            azimuth += 180
        return azimuth

    @staticmethod
    def as_less_than_90_azimuth(azimuth):
        """Make abs(azimuth) < 90."""
        if azimuth > 90:  # TODO: check 90
            azimuth -= 180
        elif azimuth < -90:
            azimuth += 180
        return azimuth


class PolygonRotator:
    def __init__(self, poly: Polygon, delta1, delta2):
        self.poly = poly
        self.delta1 = delta1
        self.delta2 = delta2
        self.rotation_check = False

    def rotate_by_angle(self, angle) -> None:
        """QgsGeometry.rotate() takes any positive and negative values. Positive - rotate clockwise,
        negative - counterclockwise.
        """
        self.poly.geom.rotate(angle, self.poly.center)
        self.poly.poly.setGeometry(self.poly.geom)
        self.rotation_check = True

    def rotate_by_longest_edge(self, length1, length2) -> None:
        if length1 > length2:
            self.rotate_by_angle(self.delta1)
        elif length1 < length2:
            self.rotate_by_angle(self.delta2)
        else:
            self.rotate_by_lower_angle()

    def rotate_by_lower_angle(self) -> None:
        self.rotate_by_angle(self.delta2) if abs(self.delta1) > abs(self.delta2) else self.rotate_by_angle(self.delta1)
