from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

import pytest
from qgis import processing
from qgis.core import (
    QgsFeature,
    QgsGeometry,
    QgsProcessingContext,
    QgsProcessingOutputLayerDefinition,
    QgsVectorLayer,
)

from PolygonsParallelToLine.src import const
from PolygonsParallelToLine.src.algorithm import Algorithm

if TYPE_CHECKING:
    from qgis.core import QgsVectorDataProvider

GRID_SIZE = 32
BUDGET_SECONDS = 0.25
SQUARE_HALF = 0.4
SPACING = 2.0
ROTATION_OFFSET_DEG = 15.0


def _rotated_square_wkt(cx: float, cy: float, half: float, angle_deg: float) -> str:
    theta = math.radians(angle_deg)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    offsets = [(-half, -half), (half, -half), (half, half), (-half, half), (-half, -half)]
    pts = [(cx + dx * cos_t - dy * sin_t, cy + dx * sin_t + dy * cos_t) for dx, dy in offsets]
    coords = ", ".join(f"{x} {y}" for x, y in pts)
    return f"Polygon (({coords}))"


def _grid_polygons() -> list[str]:
    return [
        _rotated_square_wkt(i * SPACING, j * SPACING, SQUARE_HALF, ROTATION_OFFSET_DEG)
        for i in range(GRID_SIZE)
        for j in range(GRID_SIZE)
    ]


def _diagonal_lines() -> list[str]:
    extent = (GRID_SIZE - 1) * SPACING
    return [
        f"LineString (0 0, {extent} {extent})",
        f"LineString (0 {extent}, {extent} 0)",
        f"LineString (0 {extent / 2}, {extent} {extent / 2})",
        f"LineString ({extent / 2} 0, {extent / 2} {extent})",
        f"LineString (0 {extent / 4}, {extent} {3 * extent / 4})",
    ]


@pytest.mark.perf
def test_perf_smoke_grid_1024_polygons(qgis_processing, add_features):
    line_layer = QgsVectorLayer("linestring", "temp_line", "memory")
    add_features(vector_layer=line_layer, wkt_geometries=tuple(_diagonal_lines()))

    poly_layer = QgsVectorLayer("polygon", "temp_poly", "memory")
    add_features(vector_layer=poly_layer, wkt_geometries=tuple(_grid_polygons()))

    params = {
        "REFERENCE_LAYER": line_layer,
        "POLYGON_LAYER": poly_layer,
        "LONGEST": False,
        "NO_MULTI": False,
        "DISTANCE": 0.0,
        "ANGLE": 89.9,
        "OUTPUT": QgsProcessingOutputLayerDefinition("TEMPORARY_OUTPUT"),
    }
    context = QgsProcessingContext()

    start = time.perf_counter()
    result = processing.run(algOrName=Algorithm(), parameters=params, context=context)
    elapsed = time.perf_counter() - start

    output_layer = context.getMapLayer(result[Algorithm.OUTPUT_LAYER])
    rotated_flags = [x[const.COLUMN_NAME] for x in output_layer.getFeatures()]
    assert len(rotated_flags) == GRID_SIZE * GRID_SIZE
    # Guard against a no-op fast path silently making the budget meaningless.
    assert any(rotated_flags)

    assert elapsed < BUDGET_SECONDS, f"Rotating {GRID_SIZE**2} polygons took {elapsed:.3f}s (budget {BUDGET_SECONDS}s)"


@pytest.fixture(scope="module")
def add_features():
    def add_wkt_features_to_layer(vector_layer: QgsVectorLayer, wkt_geometries: tuple[str, ...]) -> None:
        data_provider: QgsVectorDataProvider = vector_layer.dataProvider()
        for wkt_geometry in wkt_geometries:
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromWkt(wkt_geometry))
            data_provider.addFeature(feature)

    return add_wkt_features_to_layer
