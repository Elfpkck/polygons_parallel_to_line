FROM qgis/qgis:latest
RUN pip uninstall opencv-python && pip install --no-cache-dir pytest-qgis opencv-python-headless
