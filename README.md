[![PR Validation](https://github.com/Elfpkck/polygons_parallel_to_line/actions/workflows/test.yaml/badge.svg?event=pull_request)](https://github.com/Elfpkck/polygons_parallel_to_line/actions/workflows/test.yaml)
[![codecov](https://codecov.io/gh/Elfpkck/polygons_parallel_to_line/graph/badge.svg?token=QEHFI3XE08)](https://codecov.io/gh/Elfpkck/polygons_parallel_to_line)

[![QGIS](https://qgis.github.io/qgis-uni-navigation/logo.svg)](https://qgis.org)

# Polygons Parallel to Line - QGIS Python Plugin

A QGIS plugin that rotates polygons (and lines) to be parallel to a reference line. Two entry points: a batch Processing algorithm that operates on whole layers, and an interactive map tool that lets you pick a reference line on the canvas and then click — or drag-rectangle — individual line/polygon features to rotate them in place.

[Polygons Parallel to Line Plugin on QGIS Plugins Web Portal](https://plugins.qgis.org/plugins/PolygonsParallelToLine/)

![Plugin Demo][intro]

## Table of Contents
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Features](#features)
- [Algorithm](#algorithm)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Requirements](#requirements)
- [Best Practices](#best-practices)
- [Development](#development)
- [License](#license)
- [Support](#support)

## Installation

### Method 1: QGIS Plugin Manager (Recommended)
1. Open QGIS
2. Go to **Plugins** → **Manage and Install Plugins**
3. Search for "Polygons Parallel to Line"
4. Click **Install Plugin**

![Installation Guide][install]

### Method 2: Manual Installation
1. Download the plugin from the [QGIS Plugins Repository](https://plugins.qgis.org/plugins/PolygonsParallelToLine/)
2. Extract to your QGIS plugins directory
3. Restart QGIS and enable the plugin

## Quick Start

### Batch (Processing algorithm)
1. **Access the Plugin**: Go to **Processing** → **Toolbox** → **Polygons parallel to lines**
2. **Select Input Layers**: Choose your polygon and line layers
3. **Configure Parameters**: Set distance and angle thresholds as needed
4. **Run**: Execute the algorithm to generate aligned polygons

![How to Access][open]

### Interactive (map tool)
1. Open the **Polygons Parallel to Line** toolbar (also reachable from **Vector** → **Polygons Parallel to Line**) and click the **Parallel to Line (interactive)** action.
2. Click a line feature — or drag a rectangle over one — to set it as the reference. The reference is highlighted on the canvas.
3. Toggle editing on the layers you want to modify, then either click a single line/polygon to rotate it, or drag a rectangle to rotate every line/polygon feature that intersects it across all editable visible layers.
4. Use the **Settings…** action on the same toolbar to choose between rotation strategies (currently *Rotate by longest segment*). Settings persist via `QSettings`.
5. Right-click or press **Esc** to clear the reference; press **Esc** again to deactivate the tool.

## Features

✅ **Two modes**: batch Processing algorithm for whole layers, plus an interactive map-canvas tool for one-off rotations  
✅ **Automatic Polygon Rotation**: Rotates polygons to align with the nearest line  
✅ **Line-target support (interactive)**: the map tool can rotate line features too, not just polygons  
✅ **Bulk drag-rectangle**: rotate every line/polygon intersecting a rectangle across all editable visible layers — wrapped per-layer in undo-able edit commands  
✅ **CRS-aware**: reference and targets across layers in different CRSes are reconciled via `QgsCoordinateTransform`  
✅ **Distance-based Filtering**: Optional maximum distance constraint (batch mode)  
✅ **Angle Threshold Control**: Configurable angle threshold that gates which polygons are rotated (batch mode)  
✅ **Multipolygon Handling**: Multipolygons are processed (or can be skipped) — see Keynotes for behavior  
✅ **Rotation Tracking**: Adds a `_rotated` boolean field marking which polygons were modified (batch mode)  

## Algorithm

The plugin processes each polygon using the following steps:

1. **Closest Line Selection**: Finds the line whose feature is the nearest neighbor of the polygon centroid

2. **Distance Check**: If `Max distance from line` > 0 and the polygon-to-line geometry distance (closest edge of the polygon to the closest line) exceeds it → skip rotation

3. **Vertex Analysis**: Identifies the polygon vertex closest to the nearest line

4. **Segment Evaluation**: Takes the two polygon segments adjacent to that vertex

5. **Angle Calculation**: Computes the signed angle (delta azimuth) between the closest line segment and each adjacent polygon segment

6. **Rotation Decision** (each delta is compared against `Max angle`):
   - If both deltas are within `Max angle`:
     - **Longest segment mode**: Rotates by the delta of the longer segment (falls back to smallest delta if lengths are equal)
     - **Default mode**: Rotates by the smaller delta
   - If only one delta is within `Max angle`: Rotates by that delta
   - If neither delta is within `Max angle`: No rotation is applied
   - Rotations whose magnitude is effectively zero are skipped (avoids spurious `_rotated=True`)

7. **Output Generation**: Writes the (possibly rotated) geometry with a `_rotated` boolean attribute

![Default Usage][default_usage]

### Keynotes
- Rotation center is the polygon centroid (for multipolygons: the overall centroid of the whole multi-geometry)
- Interior rings and duplicate vertices are ignored when picking the rotation pivot, but they are preserved in the output geometry
- Multipolygons are rotated as a single rigid body around the overall centroid by the angle chosen from the part that contains the closest vertex — individual parts are not aligned independently
- The `_rotated` field indicates transformation status (boolean)

![Rotated Field][_rotated]

## Configuration

### Max Distance from Line
- **Type**: Float (optional)
- **Range**: ≥ 0.0
- **Default**: 0.0 (processes all polygons)
- **Unit**: Line layer CRS units

When set to 0.0, all polygons are processed regardless of distance.

![Distance Configuration][distance]

### Max Angle for Rotation
- **Type**: Float (optional)  
- **Range**: 0.0 - 89.9 degrees
- **Default**: 89.9
- **Purpose**: Threshold on the angle between a polygon segment and the closest line segment. A polygon is only rotated when at least one of its two adjacent segments has a delta angle within this threshold; otherwise the polygon is left unrotated. The applied rotation is bounded by this threshold.

![Angle Configuration][angle]

### Rotate by Longest Segment
- **Type**: Boolean
- **Default**: False
- **Behavior**: When both segments have valid angles (≤ Max angle), prioritizes the longest segment

![Longest Segment Option][by_longest]

### Skip Multipolygons
- **Type**: Boolean
- **Default**: False
- **Purpose**: When enabled, multipolygon features are passed through to the output unchanged (with `_rotated=False`) instead of being rotated. They are not removed from the output layer.

## Usage Examples

### Basic Usage
**Input**: Building polygons + Road centerlines  
**Output**: Buildings aligned parallel to the nearest roads

### Advanced Filtering
**Max Distance**: 50.0 (meters)  
**Max Angle**: 45.0 (degrees)  
**Result**: Only buildings within 50 m of roads, with rotation ≤ 45°

## Requirements

- **QGIS**: 3.0 or higher
- **Dependencies**: Standard QGIS processing framework

### Compatibility
- ✅ Windows
- ✅ macOS  
- ✅ Linux

## Best Practices

⚠️ **Important**: Validate and fix geometry errors before running the plugin for optimal results.

### Recommended Workflow
1. **Prepare Data**: Ensure polygon and line layers are in the same CRS
2. **Fix Geometries**: Use **Processing Toolbox** → **Vector geometry** → **Fix Geometries**
3. **Test Parameters**: Start with default settings on a small dataset
4. **Batch Process**: Apply to full dataset with optimized parameters

### Performance Tips
- Use spatial indexes for large datasets
- Consider processing in smaller batches for huge datasets
- Test different parameter combinations on representative samples

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development setup and contribution guidelines.

## License

Copyright (C) 2016-2026 by Andrii Liekariev

This project is licensed under the [GNU General Public License v2.0 or later](LICENSE.txt).

## Support

- 🐛 [Report Issues](https://github.com/Elfpkck/polygons_parallel_to_line/issues)
- 💬 [Discussion Forum](https://github.com/Elfpkck/polygons_parallel_to_line/discussions)

---

**Made with ❤️ for the QGIS community**

<!-- Image References -->
[intro]: https://raw.githubusercontent.com/Elfpkck/pptl_images/refs/heads/master/intro.gif
[install]: https://raw.githubusercontent.com/Elfpkck/pptl_images/refs/heads/master/install.gif
[open]: https://raw.githubusercontent.com/Elfpkck/pptl_images/refs/heads/master/open.gif
[default_usage]: https://raw.githubusercontent.com/Elfpkck/pptl_images/refs/heads/master/default_usage.gif
[_rotated]: https://raw.githubusercontent.com/Elfpkck/pptl_images/refs/heads/master/_rotated.png
[distance]: https://raw.githubusercontent.com/Elfpkck/pptl_images/refs/heads/master/distance.gif
[angle]: https://raw.githubusercontent.com/Elfpkck/pptl_images/refs/heads/master/angle.gif
[by_longest]: https://raw.githubusercontent.com/Elfpkck/pptl_images/refs/heads/master/by_longest.gif
