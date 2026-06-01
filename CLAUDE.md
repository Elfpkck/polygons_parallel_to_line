# CLAUDE.md

## Project

QGIS Processing plugin `PolygonsParallelToLine` (id `pptl`) — rotates polygons to align with the nearest line feature. Distributed via the QGIS plugin portal. Version lives in **both** `PolygonsParallelToLine/metadata.txt` (`version=`) and `pyproject.toml` (`version =`) — keep them in sync when bumping.

## Environment

Tests require QGIS Python bindings, so everything runs inside the `qgis_pptl` Docker container (image `qgis/qgis:3.44.7`, repo mounted at `/pptl`). The host `.venv` is *shadowed* inside the container by an anonymous volume — host installs are not visible to the container.

See `Makefile` for build/run/install/test targets (all `make` invocations assume the container is running).

Single test inside the container:

```shell
docker exec -t qgis_pptl sh -c "cd /pptl && uv run --no-dev pytest /pptl/tests/test_azimuth.py[::test_name] --qgis_disable_gui"
```

Lint/format runs host-side via `pre-commit`. `ruff` is `select = ["ALL"]` with per-file ignores in `pyproject.toml` — when adding ignores, narrow per-file rather than expanding globals.

## Architecture

QGIS discovery chain:

```
PolygonsParallelToLine/__init__.py::classFactory → Plugin.initProcessing → Provider.loadAlgorithms → Algorithm
```

`Algorithm` (`src/algorithm.py`) declares the processing UI (parameter IDs `LINE_LAYER`, `POLYGON_LAYER`, `LONGEST`, `NO_MULTI`, `DISTANCE`, `ANGLE`) and delegates to `PolygonsParallelToLine` in `src/pptl.py` via a `Params` dataclass (fields `by_longest`, `no_multi`, `distance`, `angle`).

`PolygonsParallelToLine.process_polygon` per-feature pipeline:

1. Wrap feature in `Polygon` (`src/polygon.py`) — `geom`, `is_multi`, `center_xy`, `is_rotated`.
2. Wrap line source in `LineLayer` (`src/line.py`) — `QgsSpatialIndex` (with `FlagStoreFeatureGeometries`) plus an `id → QgsFeature` dict for `get_closest_line(point)`.
3. Short-circuit (no rotation) if `params.distance` is truthy and centroid→line distance exceeds it, or if `is_multi and no_multi`.
4. Hand off to `PolygonRotator` (`src/rotator.py`): finds the polygon vertex closest to the line, derives the two adjacent polygon segments, computes delta-azimuths against the closest line segment using helpers in `src/azimuth.py`.
5. Rotation strategy: if both adjacent deltas are within `angle_threshold`, rotate by the longest segment (when `by_longest`) or by the smallest angle; if only one is within threshold, rotate by that one. Rotations within `ABSOLUTE_TOLERANCE` of 0 are skipped (avoids spurious `_rotated=True`).
6. Append a feature to the output sink with a `_rotated` boolean attribute (name in `src/const.py::COLUMN_NAME`).

Invariants:

- Azimuth math (`src/azimuth.py`) normalizes to `[0, 180]` then `[-90, 90]` so the delta is the minimal signed rotation.
- `Segment.length` / `Segment.azimuth` are `cached_property` — segments are immutable after construction.
- Interior rings and duplicate vertices are stripped *only* in a temp geometry inside `Polygon.get_adjacent_segments` so they don't influence the rotation pivot; the original geometry is preserved for the actual rotate.

## Testing

`tests/test_main_functionality.py` is the integration suite — builds in-memory `QgsVectorLayer`s from WKT, runs the pipeline via `processing.run(algOrName=Algorithm(), ...)`, compares output WKT. Extend the existing `@pytest.mark.parametrize` table for new cases rather than adding files. Other `tests/test_*.py` files are module unit tests and don't need a full processing run.

## Packaging & Remote Debugging

See `DEVELOPMENT.md` for the plugin-portal zip command (must zip *only* `PolygonsParallelToLine/`, not the repo root) and the PyCharm `pydevd_pycharm.settrace` setup (port `53100`, commented stubs in `src/pptl.py` and `tests/test_main_functionality.py`).
