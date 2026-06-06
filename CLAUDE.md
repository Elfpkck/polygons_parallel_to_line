# CLAUDE.md

## Project

QGIS Processing plugin `PolygonsParallelToLine` (id `pptl`) — rotates polygons to align with the nearest line feature. Distributed via the QGIS plugin portal. Releases are tag-driven via `.github/workflows/release.yaml`; `qgis-plugin-ci` patches `metadata.txt`'s `version=` and `changelog=` in the zip at build time. In-repo `version=` strings are placeholders (`0.0.0`).

## Environment

Tests require QGIS Python bindings, so everything runs inside the `qgis_pptl` Docker container (image `qgis/qgis:4.0.0`, repo mounted at `/pptl`). The host `.venv` is *shadowed* inside the container by an anonymous volume — host installs are not visible to the container.

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

## Map tool

Alongside the Processing algorithm, `Plugin.initGui` registers a dedicated "Polygons Parallel to Line" `QToolBar` (objectName `PolygonsParallelToLineToolBar`) with two `QAction`s: the interactive parallelize toggle that activates `ParallelToLineMapTool` (`src/map_tool.py`) on the canvas, and a Settings action that opens `MapToolSettingsDialog` (`src/settings_dialog.py`) to edit `MapToolSettings` (`src/settings.py`). `MapToolSettings` owns live tool state (currently just `by_longest`) and persists it via `QSettings` under the `PolygonsParallelToLine/map_tool/` prefix; the map tool reads `self.settings.by_longest` at each operation. The tool has two states: first click sets a reference line (highlighted with a `QgsRubberBand`); after that, a single click identifies and rotates one line/polygon target, while a click-and-drag draws a selection rectangle (`QgsRubberBand` polygon) and on release rotates every line/polygon feature whose geometry intersects the rectangle across all editable visible layers — wrapped per-layer in `beginEditCommand`/`endEditCommand`. Drag-rectangle is gated on the reference being set. Single clicks use `QgsMapToolIdentify.TopDownAll` so the tool walks through identify results top-down and picks the first one whose geometry type matches the current state's needs (line when no reference is set; line or polygon when one is). All cross-CRS work goes through `QgsCoordinateTransform` against `QgsProject.instance()`: the reference is stored in the map (canvas) CRS — transformed once at set time from the source layer's CRS — and `_reference_for_layer` re-projects it into each target layer's CRS at rotation time, while filter rectangles are transformed via `transformBoundingBox`. All math is delegated to `compute_parallel_geometry` in `src/parallelizer.py`, which reuses `Line`, `Segment`, `calc_delta_azimuth`, and `PolygonRotator` from the batch pipeline — pivot is the target's centroid. Right-click or `Esc` clears the reference (or cancels an in-progress drag).

## Testing

`tests/test_main_functionality.py` is the integration suite — builds in-memory `QgsVectorLayer`s from WKT, runs the pipeline via `processing.run(algOrName=Algorithm(), ...)`, compares output WKT. Extend the existing `@pytest.mark.parametrize` table for new cases rather than adding files. Other `tests/test_*.py` files are module unit tests and don't need a full processing run.

`tests/test_performance.py` is a perf smoke test marked `perf` — skipped by default via `addopts = "-m 'not perf'"` in `pyproject.toml`, run via `make test-perf`. Catches order-of-magnitude regressions in the per-feature pipeline.

## Packaging & Remote Debugging

See `DEVELOPMENT.md` for the plugin-portal zip command (must zip *only* `PolygonsParallelToLine/`, not the repo root) and the PyCharm `pydevd_pycharm.settrace` setup (port `53100`, commented stubs in `src/pptl.py` and `tests/test_main_functionality.py`).
