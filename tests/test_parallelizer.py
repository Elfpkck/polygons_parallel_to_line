from __future__ import annotations

import math

import pytest
from qgis.core import QgsGeometry, QgsPointXY

from PolygonsParallelToLine.src.azimuth import calc_delta_azimuth
from PolygonsParallelToLine.src.parallelizer import compute_parallel_geometry


def _delta_to_reference(target_wkt: str, reference_wkt: str, *, by_longest: bool) -> float:
    target = QgsGeometry.fromWkt(target_wkt)
    reference = QgsGeometry.fromWkt(reference_wkt)
    centroid = target.centroid().asPoint()
    _, _, next_idx, _ = reference.closestSegmentWithContext(centroid)
    ref_az = QgsPointXY(reference.vertexAt(next_idx - 1)).azimuth(QgsPointXY(reference.vertexAt(next_idx)))

    parts = target.asGeometryCollection() or [target]
    candidates: list[tuple[float, float]] = []  # (length, azimuth)
    for part in parts:
        verts = list(part.vertices())
        for i in range(len(verts) - 1):
            a, b = QgsPointXY(verts[i]), QgsPointXY(verts[i + 1])
            candidates.append((a.distance(b), a.azimuth(b)))

    if by_longest:
        _, chosen_az = max(candidates, key=lambda c: c[0])
    else:
        _, chosen_az = min(candidates, key=lambda c: abs(calc_delta_azimuth(ref_az, c[1])))
    return calc_delta_azimuth(ref_az, chosen_az)


REFERENCE_HORIZONTAL = "LineString (0 0, 100 0)"
REFERENCE_MULTI_SEGMENT = "LineString (0 0, 50 0, 100 5)"


@pytest.mark.parametrize(
    "reference, target, target_kind, by_longest, expect_none",
    [
        # Single-segment target rotated 30 degrees off horizontal -> non-trivial rotation.
        (REFERENCE_HORIZONTAL, "LineString (40 50, 60 60)", "line", True, False),
        # Multi-segment line target.
        (REFERENCE_HORIZONTAL, "LineString (40 50, 60 60, 80 55)", "line", True, False),
        # Same multi-segment line with by_longest=False -> uses smallest-angle segment.
        (REFERENCE_HORIZONTAL, "LineString (40 50, 60 60, 80 55)", "line", False, False),
        # Polygon target.
        (REFERENCE_HORIZONTAL, "Polygon ((10 50, 30 70, 50 55, 30 35, 10 50))", "polygon", False, False),
        # Polygon target via by_longest.
        (REFERENCE_HORIZONTAL, "Polygon ((10 50, 30 70, 50 55, 30 35, 10 50))", "polygon", True, False),
        # Multi-segment reference, line target.
        (REFERENCE_MULTI_SEGMENT, "LineString (30 30, 60 50)", "line", True, False),
        # Already parallel (horizontal target vs horizontal reference) -> None.
        (REFERENCE_HORIZONTAL, "LineString (10 40, 50 40)", "line", True, True),
        # Near-90-degree edge: vertical target line.
        (REFERENCE_HORIZONTAL, "LineString (40 20, 40 80)", "line", True, False),
    ],
    ids=[
        "single_segment_line",
        "multi_segment_line_by_longest",
        "multi_segment_line_by_smallest_angle",
        "polygon_by_smallest_angle",
        "polygon_by_longest",
        "multi_segment_reference",
        "already_parallel_returns_none",
        "perpendicular_line",
    ],
)
def test_compute_parallel_geometry(qgis_app, reference, target, target_kind, by_longest, expect_none):
    ref_geom = QgsGeometry.fromWkt(reference)
    target_geom = QgsGeometry.fromWkt(target)

    result = compute_parallel_geometry(ref_geom, target_geom, target_kind, by_longest=by_longest)

    if expect_none:
        assert result is None
        return

    assert result is not None
    # Centroid is preserved by rotation.
    assert result.centroid().asPoint().distance(target_geom.centroid().asPoint()) < 1e-6

    if target_kind == "line":
        residual = _delta_to_reference(result.asWkt(), reference, by_longest=by_longest)
        assert math.isclose(residual, 0.0, abs_tol=1e-6)
