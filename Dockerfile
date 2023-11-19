FROM qgis/qgis:latest
RUN pip install --no-cache-dir pytest-qgis pydevd-pycharm
