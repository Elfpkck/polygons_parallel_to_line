FROM qgis/qgis:latest
RUN pip install --no-cache-dir pytest-qgis pydevd-pycharm && tail -f /dev/null
