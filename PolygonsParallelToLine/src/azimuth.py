from __future__ import annotations


def normalize_azimuth_to_positive_range(azimuth: float) -> float:
    if azimuth == -180:
        azimuth = 180
    elif azimuth < 0:
        azimuth += 180
    return azimuth


def normalize_azimuth_to_90_range(azimuth: float) -> float:
    if azimuth > 90:
        azimuth -= 180
    elif azimuth < -90:
        azimuth += 180
    return azimuth


def calc_delta_azimuth(segment_azimuth: float, line_azimuth: float) -> float:
    return normalize_azimuth_to_90_range(
        normalize_azimuth_to_positive_range(segment_azimuth) - normalize_azimuth_to_positive_range(line_azimuth)
    )
