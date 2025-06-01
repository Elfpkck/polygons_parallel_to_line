def normalize_azimuth_to_positive_range(azimuth: float) -> float:
    """
    Normalizes an azimuth to the positive range [0, 180].

    In azimuth calculations, angles of -180° to 0° are equivalent to
    angles of 0° to 180° in the opposite direction. This function
    converts all azimuths to their positive representation.

    Args:
        azimuth: The input azimuth in degrees

    Returns:
        The equivalent azimuth in the range [0, 180]
    """
    if azimuth == -180:
        azimuth = 180
    elif azimuth < 0:
        azimuth += 180
    return azimuth


def normalize_azimuth_to_90_range(azimuth: float) -> float:
    """
    Normalize azimuth angle to be within the range [-90, 90] degrees.

    This function takes any azimuth angle and converts it to an equivalent angle
    within the range of -90 to 90 degrees by adding or subtracting 180 degrees
    as needed.

    Args:
        azimuth: The azimuth angle in degrees to normalize

    Returns:
        The normalized azimuth angle within [-90, 90] degrees
    """
    if azimuth > 90:
        azimuth -= 180
    elif azimuth < -90:
        azimuth += 180
    return azimuth


def calc_delta_azimuth(segment_azimuth: float, line_azimuth: float) -> float:
    return normalize_azimuth_to_90_range(
        normalize_azimuth_to_positive_range(segment_azimuth) - normalize_azimuth_to_positive_range(line_azimuth)
    )
