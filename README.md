[![PR Validation](https://github.com/Elfpkck/polygons_parallel_to_line/actions/workflows/test.yaml/badge.svg?event=pull_request)](https://github.com/Elfpkck/polygons_parallel_to_line/actions/workflows/test.yaml)
[![codecov](https://codecov.io/gh/Elfpkck/polygons_parallel_to_line/graph/badge.svg?token=QEHFI3XE08)](https://codecov.io/gh/Elfpkck/polygons_parallel_to_line)

[![QGIS](https://qgis.github.io/qgis-uni-navigation/logo.svg)](https://qgis.org)

# Polygons Parallel to Line — QGIS Python Plugin

A QGIS processing plugin that automatically rotates polygons to align them parallel with their nearest lines based on configurable parameters.

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

1. **Access the Plugin**: Go to **Processing** → **Toolbox** → **Polygons Parallel to Line**
2. **Select Input Layers**: Choose your polygon and line layers
3. **Configure Parameters**: Set distance and angle thresholds as needed
4. **Run**: Execute the algorithm to generate aligned polygons

![How to Access][open]

## Features

✅ **Automatic Polygon Rotation**: Intelligently rotates polygons to align with nearest lines  
✅ **Distance-based Filtering**: Optional maximum distance constraint  
✅ **Angle Threshold Control**: Configurable rotation angle limits  
✅ **Multigeometry Support**: Handles both simple and complex geometries  
✅ **Rotation Tracking**: Adds `_rotated` field to track which polygons were modified  
✅ **Geometry Validation**: Built-in checks for geometry integrity  

## Algorithm

The plugin processes each polygon using the following steps:

1. **Distance Check**: Calculates distance from polygon centroid to nearest line
   - If `Max distance from line` > 0 and distance exceeds threshold → skip polygon

2. **Vertex Analysis**: Identifies the closest polygon vertex to the nearest line

3. **Segment Evaluation**: Analyzes two adjacent segments of the closest vertex

4. **Angle Calculation**: Computes rotation angles between line segment and polygon segments

5. **Rotation Decision**:
   - If both angles ≤ `Max angle`:
     - **Longest segment mode**: Rotates based on longest segment (or smallest angle if equal)
     - **Default mode**: Rotates based on smallest angle
   - If only one angle ≤ `Max angle`: Rotates based on that segment

6. **Output Generation**: Creates rotated geometry with `_rotated` field indicator

![Default Usage][default_usage]

### Key Notes
- Rotation center is the polygon centroid
- Interior rings and duplicate vertices are ignored
- Multipolygons use the same principles as simple polygons
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
- **Purpose**: Limits maximum rotation angle

![Angle Configuration][angle]

### Rotate by Longest Segment
- **Type**: Boolean
- **Default**: False
- **Behavior**: When both segments have valid angles (≤ Max angle), prioritizes the longest segment

![Longest Segment Option][by_longest]

### Skip Multipolygons
- **Type**: Boolean
- **Default**: False
- **Purpose**: Excludes multipolygon geometries from processing

## Usage Examples

### Basic Usage
**Input**: Building polygons + Road centerlines  
**Output**: Buildings aligned parallel to nearest roads

### Advanced Filtering
**Max Distance**: 50.0 (meters)  
**Max Angle**: 45.0 (degrees)  
**Result**: Only buildings within 50m of roads, with rotation ≤ 45°

## Requirements

- **QGIS**: 3.0 or higher
- **Dependencies**: Standard QGIS processing framework

### Compatibility
- ✅ Windows
- ✅ macOS  
- ✅ Linux
- ✅ All QGIS LTR versions

## Best Practices

⚠️ **Important**: Validate and fix geometry errors before running the plugin for optimal results.

### Recommended Workflow
1. **Prepare Data**: Ensure polygon and line layers are in the same CRS
2. **Fix Geometries**: Use **Processing Toolbox** → **Vector geometry** → **Fix Geometries**
3. **Test Parameters**: Start with default settings on a small dataset
4. **Batch Process**: Apply to full dataset with optimized parameters

### Performance Tips
- Use spatial indexes for large datasets
- Consider processing in smaller batches for very large datasets
- Test different parameter combinations on representative samples

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development setup and contribution guidelines.

## License

Copyright (C) 2016-2025 by Andrii Liekariev

This project is licensed under the [GNU General Public License v2.0](LICENSE.txt).

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
