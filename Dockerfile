FROM qgis/qgis:latest
RUN pip install --no-cache-dir --break-system-packages pytest-qgis pydevd-pycharm
