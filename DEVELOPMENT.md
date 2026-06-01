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

## Add a New Plugin Version to QGIS

1. Run:
   ```shell
   zip -r pptl.zip PolygonsParallelToLine/ -x "*.DS_Store" "__MACOSX" "*/__pycache__/*" "*.pyc" "*.pyo" "*~" "*.bak"
   ```
2. Open https://plugins.qgis.org/plugins/PolygonsParallelToLine/version/add/
3. Upload `pptl.zip`
