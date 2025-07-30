FROM --platform=linux/amd64 qgis/qgis:3.44.1

# `--break-system-packages` allows installing poetry to system Python
# `system-site-packages` is required to access QGIS libraries from the virtual environment (qgis is not in PyPI)
RUN pip install --no-cache-dir --break-system-packages poetry && \
    poetry config virtualenvs.options.system-site-packages true && \
    poetry config installer.max-workers 10  && \
    poetry config installer.parallel true

# Keep container running for exec commands from Makefile
CMD ["tail", "-f", "/dev/null"]
