from __future__ import annotations

import math
from typing import Literal

from qgis.core import Qgis, QgsFeature, QgsGeometry

from .azimuth import calc_delta_azimuth
from .reference import ReferenceFeature, Segment, iter_segments
from .rotator import TargetRotator
from .target import Target

ABSOLUTE_TOLERANCE = 1e-8


def compute_parallel_geometry(  # noqa: PLR0913
    reference_geom: QgsGeometry,
    target_geom: QgsGeometry,
    target_kind: Literal["line", "polygon"],
    *,
    by_longest: bool,
    target_segment: Segment | None = None,
    angle_threshold: float = math.inf,
) -> QgsGeometry | None:
    reference = ReferenceFeature.from_geometry(reference_geom)

    if target_kind == "polygon" and target_segment is None:
        target_feature = QgsFeature()
        target_feature.setGeometry(target_geom)
        target = Target(target_feature)
        TargetRotator(
            target=target,
            closest_reference=reference,
            angle_threshold=angle_threshold,
            by_longest=by_longest,
        ).rotate()
        return QgsGeometry(target.geom) if target.is_rotated else None

    centroid_xy = target_geom.centroid().asPoint()
    ref_segment = reference.get_closest_segment(centroid_xy)
    chosen_target_segment = (
        target_segment
        if target_segment is not None
        else _pick_target_segment(target_geom, ref_segment, by_longest=by_longest)
    )
    delta = calc_delta_azimuth(ref_segment.azimuth, chosen_target_segment.azimuth)

    if abs(delta) > angle_threshold:
        return None

    if math.isclose(delta, 0.0, abs_tol=ABSOLUTE_TOLERANCE):
        return None

    rotated = QgsGeometry(target_geom)
    if rotated.rotate(delta, centroid_xy) != Qgis.GeometryOperationResult.Success:
        return None
    return rotated


def _pick_target_segment(target_geom: QgsGeometry, ref_segment: Segment, *, by_longest: bool) -> Segment:
    segments = list(iter_segments(target_geom))
    if by_longest:
        return max(segments, key=lambda s: s.length)
    return min(segments, key=lambda s: abs(calc_delta_azimuth(ref_segment.azimuth, s.azimuth)))
