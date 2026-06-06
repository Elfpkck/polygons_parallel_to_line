# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]
- Add an interactive map tool: pick a reference line on the canvas, then click — or drag a rectangle — to rotate individual line/polygon features (or every feature in the rectangle across editable visible layers) parallel to it
- Add a Settings dialog (toggle "Rotate by longest segment"); choices persist via `QSettings`
- Reconcile reference and target geometries when layers are in different CRSes
- Register a "Polygons Parallel to Line" toolbar and Vector-menu entry

## [1.2.0] - 2026-06-01
- Enhance polygon rotation logic and geometry validation
- Fix `no_multi` regression
- Test against QGIS 4.0
- Automate releases via tag-triggered `qgis-plugin-ci` pipeline

## [1.1.0] - 2025-06-13
- Enhance UI text readability
- Skip rotation when an angle is close to zero to avoid unnecessary operations and wrong "_rotated" values
- Handle polygon vertex duplicates and internal rings properly
- Update test cases to cover new edge cases

## [1.0.0] - 2023-11-19
- Add QGIS 3 support
- Add tests
- Fix bugs

## [0.3.0] - 2017-04-05
- Migrate to Processing algorithms; full refactoring
- Major performance improvements
- Add option to write all or only selected polygons to the new layer
- Add option to rotate or skip multipolygons
- Process each polyline of a multipolyline as a separate line
- Avoid duplicating the "_rotated" field if it already exists

## [0.2.1] - 2017-03-14
- Add Russian and Ukrainian translations

## [0.2.0] - 2016-04-07
- Major performance improvements via spatial index and built-in PyQGIS methods
- Add progress bar
- Add option to rotate only selected polygons
- Add "rotated" field to the polygon layer (value `1` for rotated polygons)
- New icon
- English-only code comments

## [0.1.0] - 2016-03-31
- Initial release
