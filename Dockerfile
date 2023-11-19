FROM qgis/qgis:latest
RUN pip install --no-cache-dir pytest-qgis && pip uninstall opencv-python && pip install --no-cache-dir opencv-python-headless
