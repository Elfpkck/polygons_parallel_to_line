# Local Development and Debugging Instructions

## Getting Started

1. Install Docker.
2. Run the following commands:
    ```shell
    make build
    make run
    make install
    make test
    ```

Performance smoke tests are skipped by default. Run them with `make test-perf` to catch order-of-magnitude regressions in the per-feature pipeline.

## Remote Debugging

These instructions are specific to PyCharm.

1. Set up the `uv` Python interpreter.
2. Run the following commands:
    ```shell
    uv sync
    make install-dev
    ```
3. Set up the Python Debug Server in PyCharm:
    - IDE host name: `127.0.0.1`
    - Port: `53100`
4. Add breakpoint(s) as needed.

### Docker Remote Debugging

1. Perform the additional setup for the Python Debug Server:
    - Path mappings: `<absolute/path/to/repo>=/pptl` (replace the left side with your local clone's absolute path)
2. Uncomment the following line in `tests/test_main_functionality.py`:
    ```python
    # pydevd_pycharm.settrace("host.docker.internal", port=53100, stdoutToServer=True, stderrToServer=True)
    ```
3. Add `import pydevd_pycharm` to `tests/test_main_functionality.py`.

### QGIS Remote Debugging

1. Install `pydevd-pycharm` and `pydevd` into the Python interpreter bundled with QGIS. On macOS:
    ```shell
    /Applications/QGIS.app/Contents/MacOS/bin/python3 -m pip install pydevd-pycharm pydevd
    ```
    On Linux/Windows, invoke `pip` from the QGIS-bundled Python (e.g., the `python3` shipped under the QGIS install directory).
2. Uncomment the following line in `PolygonsParallelToLine/src/pptl.py`:
    ```python
    # pydevd_pycharm.settrace("127.0.0.1", port=53100, stdoutToServer=True, stderrToServer=True)
    ```
3. Add `import pydevd_pycharm` to `PolygonsParallelToLine/src/pptl.py`.
4. In QGIS, navigate to Preferences → System → Environment, and add the following variable:
    - Apply: Append
    - Variable: `QGIS_PLUGINPATH`
    - Value: `<absolute/path/to/repo>` (the absolute path to your local clone of this repository)
5. To reload the plugin, use the "Plugin Reloader" plugin.

## Releasing a New Plugin Version

1. Move the entries under `## [Unreleased]` in `CHANGELOG.md` to a new `## [X.Y.Z] - YYYY-MM-DD` section. `qgis-plugin-ci` requires a 3-part `MAJOR.MINOR.PATCH` version — `## [1.2]` will be silently ignored and the published changelog will be empty.
2. Commit and push to `main`.
3. Tag and push (3-part versions only):
   ```shell
   git tag X.Y.Z
   git push origin X.Y.Z
   ```
4. The `Release` workflow (`.github/workflows/release.yaml`) runs the tests, then publishes to plugins.qgis.org and creates a GitHub Release with the `.zip` attached.

Required GitHub Secrets (one-time setup, repo Settings → Secrets and variables → Actions):
- `OSGEO_USERNAME` — your plugins.qgis.org account username
- `OSGEO_PASSWORD` — your plugins.qgis.org account password

(`GITHUB_TOKEN` is provided automatically by Actions.)

For a staged/experimental release, use a 3-part pre-release tag suffix (e.g. `1.2.0-rc1`). The portal will list it as experimental. A 2-part form like `1.2-rc1` is not detected as a pre-release by `qgis-plugin-ci` and will be published as stable.
