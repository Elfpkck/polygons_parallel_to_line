from __future__ import annotations

import math
from typing import TYPE_CHECKING, Literal

from qgis.core import Qgis, QgsFeature, QgsGeometry

from .azimuth import calc_delta_azimuth
from .line import Line, Segment
from .polygon import Polygon
from .rotator import PolygonRotator

if TYPE_CHECKING:
    from collections.abc import Iterator

ABSOLUTE_TOLERANCE = 1e-8


def compute_parallel_geometry(
    reference_geom: QgsGeometry,
    target_geom: QgsGeometry,
    target_kind: Literal["line", "polygon"],
    *,
    by_longest: bool,
) -> QgsGeometry | None:
    reference_line = Line(_as_feature(reference_geom))

    if target_kind == "polygon":
        target_feature = _as_feature(target_geom)
        poly = Polygon(target_feature)
        PolygonRotator(
            poly=poly,
            closest_line=reference_line,
            angle_threshold=math.inf,
            by_longest=by_longest,
        ).rotate()
        return QgsGeometry(poly.geom) if poly.is_rotated else None

    centroid_xy = target_geom.centroid().asPoint()
    ref_segment = reference_line.get_closest_segment(centroid_xy)
    target_segment = _pick_target_segment(target_geom, ref_segment, by_longest=by_longest)
    delta = calc_delta_azimuth(ref_segment.azimuth, target_segment.azimuth)

    if math.isclose(delta, 0.0, abs_tol=ABSOLUTE_TOLERANCE):
        return None

    rotated = QgsGeometry(target_geom)
    if rotated.rotate(delta, centroid_xy) != Qgis.GeometryOperationResult.Success:
        return None
    return rotated


def _as_feature(geom: QgsGeometry) -> QgsFeature:
    feature = QgsFeature()
    feature.setGeometry(geom)
    return feature


def _pick_target_segment(target_geom: QgsGeometry, ref_segment: Segment, *, by_longest: bool) -> Segment:
    segments = list(_iter_segments(target_geom))
    if by_longest:
        return max(segments, key=lambda s: s.length)
    return min(segments, key=lambda s: abs(calc_delta_azimuth(ref_segment.azimuth, s.azimuth)))


def _iter_segments(geom: QgsGeometry) -> Iterator[Segment]:
    parts = geom.asGeometryCollection() or [geom]
    for part in parts:
        verts = list(part.vertices())
        for i in range(len(verts) - 1):
            yield Segment(start=verts[i], end=verts[i + 1])
