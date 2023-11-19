FROM --platform=linux/amd64 qgis/qgis:latest
ENV DISPLAY=:99
RUN pip install --no-cache-dir pytest-qgis
