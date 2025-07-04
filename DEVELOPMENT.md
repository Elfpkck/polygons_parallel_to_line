# Local Development and Debugging Instructions

## Getting Started

1. Install Docker.
2. Run the following commands:
    ```shell
    make build
    make run
    make install-ci
    make test
    ```

## Remote Debugging

These instructions are specific to PyCharm.

1. Set up the `poetry` Python interpreter.
2. Run the following commands:
    ```shell
    poetry install
    make install-local
    ```
3. Set up the Python Debug Server in PyCharm:
    - IDE host name: `127.0.0.1`
    - Port: `53100`
4. Add breakpoint(s) as needed.

### Docker Remote Debugging

1. Perform the additional setup for the Python Debug Server:
    - Path mappings: `/Users/elf/dev/private/polygons_parallel_to_line=/pptl`
2. Uncomment the following line in `test_main_functionality.py`:
    ```python
    # pydevd_pycharm.settrace("host.docker.internal", port=53100, stdoutToServer=True, stderrToServer=True)
    ```
3. Add `import pydevd_pycharm` to `test_main_functionality.py`.

### QGIS Remote Debugging

1. Run:
    ```shell
    /Applications/QGIS.app/Contents/MacOS/bin/python3 -m pip install pydevd-pycharm pydevd
    ```
2. Uncomment the following line in `pptl.py`:
    ```python
    # pydevd_pycharm.settrace("127.0.0.1", port=53100, stdoutToServer=True, stderrToServer=True)
    ```
3. Add `import pydevd_pycharm` to `pptl.py`.
4. In QGIS, navigate to Preferences → System → Environment, and add the following variable:
    - Apply: Append
    - Variable: `QGIS_PLUGINPATH`
    - Value: `/path/to/plugin` (e.g., `/Users/elf/dev/private/polygons_parallel_to_line`)
5. To reload the plugin, use the "Plugin Reloader" plugin.

## Add a New Plugin Version to QGIS

1. Run:
   ```shell
   zip -r pptl.zip PolygonsParallelToLine/ -x "*.DS_Store" "__MACOSX" "*/__pycache__/*" "*.pyc" "*.pyo" "*~" "*.bak"
   ```
2. Open https://plugins.qgis.org/plugins/PolygonsParallelToLine/version/add/
3. Upload `pptl.zip`
