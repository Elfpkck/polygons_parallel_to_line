FROM --platform=linux/amd64 qgis/qgis:latest
RUN pip install --no-cache-dir pytest-qgis
