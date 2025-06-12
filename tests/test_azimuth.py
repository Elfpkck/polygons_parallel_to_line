from __future__ import annotations

import pytest

from PolygonsParallelToLine.src.azimuth import (
    normalize_azimuth_to_90_range,
    normalize_azimuth_to_positive_range,
)


@pytest.mark.parametrize(
    "azimuth, expected",
    [
        (0, 0),
        (90, 90),
        (180, 180),
        (-90, 90),
        (-180, 180),
        (-45, 135),
        (45, 45),
        (135, 135),
    ],
)
def test_normalize_azimuth_to_positive_range(azimuth, expected):
    """Test if the normalize_azimuth_to_positive_range function correctly normalizes azimuth values."""
    result = normalize_azimuth_to_positive_range(azimuth)
    assert result == expected


@pytest.mark.parametrize(
    "azimuth, expected",
    [
        (0, 0),  # no adjustments needed
        (45, 45),  # already within range
        (90, 90),  # edge of positive range
        (-90, -90),  # edge of negative range
        (135, -45),  # needs to loop back into range
        (-135, 45),  # loops back to positive equivalent
        (180, 0),  # falls exactly on ±180 degrees
        (-180, 0),  # normalized between edges
    ],
)
def test_normalize_azimuth_to_90_range(azimuth, expected):
    """Test if the normalize_azimuth_to_90_range function correctly normalizes azimuth values."""
    result = normalize_azimuth_to_90_range(azimuth)
    assert result == expected
