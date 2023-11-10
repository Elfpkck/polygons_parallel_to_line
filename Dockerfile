FROM --platform=linux/amd64 qgis/qgis:release-3_30
ENV DISPLAY=:99
RUN pip install --no-cache-dir pytest-qgis pydevd-pycharm && tail -f /dev/null


