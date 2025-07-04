from __future__ import annotations

import math
from typing import TYPE_CHECKING

from qgis.core import QgsPointXY

from .azimuth import calc_delta_azimuth

if TYPE_CHECKING:
    from .line import Line
    from .polygon import Polygon


class PolygonRotator:
    """
    Handles the behavior of rotating a polygon based on its segments and azimuth differences.

    This class provides methods for determining and executing rotational adjustments on a polygon. The rotation logic
    accounts for the relationship between a polygon's vertices, the adjacent segments, and the closest external line
    segment. Decisions are based on calculated azimuth differences and configurable thresholds. Optional behavior
    includes determining the rotation based on either the longest polygon segment or the smallest rotation angle.

    :ivar poly: The polygon object to be rotated.
    :type poly: Polygon
    :ivar angle_threshold: The angle threshold used to determine valid rotations.
    :type angle_threshold: float
    :ivar by_longest: Indicates whether rotation should be based on the longest segment.
    :type by_longest: bool
    :ivar prev_poly_segment: The polygon segment preceding the closest vertex.
    :type prev_poly_segment: Segment
    :ivar next_poly_segment: The polygon segment following the closest vertex.
    :type next_poly_segment: Segment
    :ivar prev_delta_azimuth: The azimuth difference between the line segment and the previous polygon segment.
    :type prev_delta_azimuth: float
    :ivar next_delta_azimuth: The azimuth difference between the line segment and the next polygon segment.
    :type next_delta_azimuth: float
    :ivar ABSOLUTE_TOLERANCE: Tolerance value for numerical closeness comparison in rotation.
    :type ABSOLUTE_TOLERANCE: float
    """

    ABSOLUTE_TOLERANCE = 1e-8

    def __init__(self, poly: Polygon, closest_line: Line, angle_threshold: float, by_longest: bool):
        self.poly = poly
        self.angle_threshold = angle_threshold
        self.by_longest = by_longest
        poly_closest_vertex = poly.get_closest_vertex(closest_line)
        self.prev_poly_segment, self.next_poly_segment = poly.get_adjacent_segments(poly_closest_vertex)
        line_segment = closest_line.get_closest_segment(QgsPointXY(poly_closest_vertex))
        self.prev_delta_azimuth = calc_delta_azimuth(line_segment.azimuth, self.prev_poly_segment.azimuth)
        self.next_delta_azimuth = calc_delta_azimuth(line_segment.azimuth, self.next_poly_segment.azimuth)

    def rotate(self) -> None:
        """
        Rotates the object based on the specified conditions and angle thresholds. The rotation logic depends on
        whether the azimuth differences, `prev_delta_azimuth` and `next_delta_azimuth`, fall within the provided angle
        threshold. If the conditions are met, it either rotates by the longest segment or by the smallest angle. It may
        also perform rotation based on the specific azimuth difference if only one of them satisfies the threshold.

        :return: None
        """
        if abs(self.prev_delta_azimuth) <= self.angle_threshold >= abs(self.next_delta_azimuth):
            if self.by_longest:
                return self.rotate_by_longest_segment()
            return self.rotate_by_smallest_angle()

        for delta_azimuth in (self.prev_delta_azimuth, self.next_delta_azimuth):
            if abs(delta_azimuth) <= self.angle_threshold:
                return self.rotate_by_angle(delta_azimuth)

    def rotate_by_angle(self, angle: float) -> None:
        """
        Rotates a polygon by a specified angle if the angle is not close to zero.

        This method checks if the provided angle is approximately zero using a tolerance value. If the angle is not
        close to zero, the method applies a rotation transformation to the polygon.

        :param angle: The angle, in degrees, by which the polygon should be rotated.
        :type angle: float
        :return: None
        """
        is_close_to_zero = math.isclose(angle, 0.0, abs_tol=self.ABSOLUTE_TOLERANCE)
        if not is_close_to_zero:
            self.poly.rotate(angle)

    def rotate_by_longest_segment(self) -> None:
        """
        Rotates an object based on the lengths of the previous and next polygon segments.

        The function compares the lengths of the previous polygon segment and the next polygon segment. If the previous
        segment is longer, the rotation is performed using the previous azimuth delta. If the next segment is longer,
        the rotation is performed using the next azimuth delta. In the case where both segments have the same length,
        the rotation is executed based on the smallest rotational angle.

        :return: None
        """
        if self.prev_poly_segment.length > self.next_poly_segment.length:
            self.rotate_by_angle(self.prev_delta_azimuth)
        elif self.prev_poly_segment.length < self.next_poly_segment.length:
            self.rotate_by_angle(self.next_delta_azimuth)
        else:
            self.rotate_by_smallest_angle()

    def rotate_by_smallest_angle(self) -> None:
        """
        Rotates the object by the smallest absolute angle difference. It compares the absolute values of the previous
        and next azimuth deltas and invokes the rotation method with the smaller magnitude delta.

        :raises ValueError: Raises an exception if the rotation operation is invalid.
        :return: This method returns nothing; it performs the operation of rotating the object using the appropriate
            azimuth delta.
        """
        if abs(self.prev_delta_azimuth) > abs(self.next_delta_azimuth):
            self.rotate_by_angle(self.next_delta_azimuth)
        else:
            self.rotate_by_angle(self.prev_delta_azimuth)
