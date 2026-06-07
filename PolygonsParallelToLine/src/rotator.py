from __future__ import annotations

import math
from typing import TYPE_CHECKING

from qgis.core import QgsPointXY

from .azimuth import calc_delta_azimuth

if TYPE_CHECKING:
    from .reference import ReferenceFeature
    from .target import Target


class TargetRotator:
    # Invoked only when the target is a polygon (via compute_parallel_geometry's
    # polygon branch); strategy picks a vertex-adjacent segment as the rotation axis.
    ABSOLUTE_TOLERANCE = 1e-8

    def __init__(
        self, target: Target, closest_reference: ReferenceFeature, angle_threshold: float, *, by_longest: bool
    ):
        self.target = target
        self.angle_threshold = angle_threshold
        self.by_longest = by_longest
        target_closest_vertex = target.get_closest_vertex(closest_reference)
        self.prev_target_segment, self.next_target_segment = target.get_adjacent_segments(target_closest_vertex)
        ref_segment = closest_reference.get_closest_segment(QgsPointXY(target_closest_vertex))
        self.prev_delta_azimuth = calc_delta_azimuth(ref_segment.azimuth, self.prev_target_segment.azimuth)
        self.next_delta_azimuth = calc_delta_azimuth(ref_segment.azimuth, self.next_target_segment.azimuth)

    def rotate(self) -> None:
        prev_within = abs(self.prev_delta_azimuth) <= self.angle_threshold
        next_within = abs(self.next_delta_azimuth) <= self.angle_threshold

        if prev_within and next_within:
            if self.by_longest:
                self.rotate_by_longest_segment()
            else:
                self.rotate_by_smallest_angle()
            return

        if prev_within:
            self.rotate_by_angle(self.prev_delta_azimuth)
        elif next_within:
            self.rotate_by_angle(self.next_delta_azimuth)

    def rotate_by_angle(self, angle: float) -> None:
        if not math.isclose(angle, 0.0, abs_tol=self.ABSOLUTE_TOLERANCE):
            self.target.rotate(angle)

    def rotate_by_longest_segment(self) -> None:
        if self.prev_target_segment.length > self.next_target_segment.length:
            self.rotate_by_angle(self.prev_delta_azimuth)
        elif self.prev_target_segment.length < self.next_target_segment.length:
            self.rotate_by_angle(self.next_delta_azimuth)
        else:
            self.rotate_by_smallest_angle()

    def rotate_by_smallest_angle(self) -> None:
        if abs(self.prev_delta_azimuth) > abs(self.next_delta_azimuth):
            self.rotate_by_angle(self.next_delta_azimuth)
        else:
            self.rotate_by_angle(self.prev_delta_azimuth)
