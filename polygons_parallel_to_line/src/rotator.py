from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.core import QgsPointXY

from .azimuth import calc_delta_azimuth

if TYPE_CHECKING:
    from .line import Line
    from .polygon import Polygon


class PolygonRotator:
    """
    Handles rotation of polygon geometries based on specific geometric relationships and constraints.

    This class facilitates the rotation of a polygon based on the azimuth angles of its segments relative to a given
    reference line. The rotation can be executed according to the smallest angle of adjustment or by prioritizing
    the longest segment. Various geometric methods are utilized to determine the azimuths, angle differences, and
    relevant polygon segments.

    :ivar poly: The polygon geometry to be rotated.
    :type poly: Polygon
    :ivar angle_threshold: The maximum angle deviation for permissible rotation.
    :type angle_threshold: float
    :ivar by_longest: A flag indicating whether the rotation prioritizes the longest segment or smallest angle.
    :type by_longest: bool
    :ivar prev_poly_segment: The polygon segment preceding the closest vertex to the reference line.
    :type prev_poly_segment: Segment
    :ivar next_poly_segment: The polygon segment following the closest vertex to the reference line.
    :type next_poly_segment: Segment
    :ivar prev_delta_azimuth: The azimuth difference between the previous polygon segment and the reference
                              line segment.
    :type prev_delta_azimuth: float
    :ivar next_delta_azimuth: The azimuth difference between the next polygon segment and the reference line segment.
    :type next_delta_azimuth: float
    """

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
        Rotates the polygon by a given angle.

        This method updates the orientation of the polygon by rotating it around its center by the specified angle.
        The rotation is applied in a clockwise direction if the angle is positive and counterclockwise if the angle is
        negative. The angle is specified in degrees.

        :param angle: The angle by which to rotate the polygon.
        :type angle: float
        :return: None
        """
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
