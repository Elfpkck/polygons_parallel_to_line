from __future__ import annotations


def normalize_azimuth_to_positive_range(azimuth: float) -> float:
    """
    Normalize an azimuth value to the positive range [0, 180].

    The function takes an azimuth value, which represents an angle in degrees, and ensures that it is expressed in its
    positive range. If the azimuth is exactly -180, it is converted to 180. If the azimuth is negative but not -180,
    the function adjusts the value to ensure it falls within the positive range of 0 to 180 degrees.

    :param azimuth: The input angle in degrees that needs to be normalized.
    :type azimuth: float
    :return: The normalized azimuth value in the range [0, 180].
    :rtype: float
    """
    if azimuth == -180:
        azimuth = 180
    elif azimuth < 0:
        azimuth += 180
    return azimuth


def normalize_azimuth_to_90_range(azimuth: float) -> float:
    """
    Normalize the provided azimuth angle to fall within the range of -90 to 90 degrees.

    This function takes an azimuth angle and adjusts it to ensure it resides within the range of -90 to 90 degrees.
    Positive azimuth angles greater than 90 are reduced by 180, and negative azimuth angles less than -90 are increased
    by 180 to keep them in the specified range.

    :param azimuth: The azimuth angle in degrees to be normalized. Expected to be a floating-point value.
    :return: The normalized azimuth angle within the range of -90 to 90 degrees.
    :rtype: float
    """
    if azimuth > 90:
        azimuth -= 180
    elif azimuth < -90:
        azimuth += 180
    return azimuth


def calc_delta_azimuth(segment_azimuth: float, line_azimuth: float) -> float:
    """
    Calculates the delta azimuth between a given segment azimuth and a line azimuth. The delta azimuth is normalized
    to fit within the range of -90 to +90 degrees.
    This function uses helper functions to normalize the azimuth values before computing the difference.

    :param segment_azimuth: Azimuth angle of the segment in degrees
    :param line_azimuth: Azimuth angle of the reference line in degrees
    :return: Normalized delta azimuth in degrees within -90 to +90 range
    :rtype: float
    """
    return normalize_azimuth_to_90_range(
        normalize_azimuth_to_positive_range(segment_azimuth) - normalize_azimuth_to_positive_range(line_azimuth)
    )
