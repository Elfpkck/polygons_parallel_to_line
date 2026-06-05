QGIS_VERSION ?= 4.0.0
IMAGE := qgis-for-pptl:$(QGIS_VERSION)
CONTAINER := qgis_pptl

.PHONY: build run install install-dev test test-coverage test-perf stop clean

build:
	DOCKER_SCAN_SUGGEST=false docker build -t $(IMAGE) -f Dockerfile .

# -v /pptl/.venv - an anonymous volume, which "shadows" the host's `.venv` directory
# --rm: container is auto-removed on stop so `make run` is idempotent across sessions
run: build
	docker run -d --rm --name $(CONTAINER) \
		-v "$(CURDIR):/pptl" \
		-v /pptl/.venv \
		-e PYTHONPATH=/pptl:/usr/share/qgis/python \
		$(IMAGE)

install:
	docker exec $(CONTAINER) sh -c "cd /pptl && uv venv --allow-existing --system-site-packages && uv sync --locked --no-dev"

# For an unknown reason, I need to add the pydevd package in this specific way to make the PyCharm remote debugger work with Docker
install-dev:
	docker exec $(CONTAINER) sh -c "cd /pptl && uv venv --allow-existing --system-site-packages && uv sync --locked && uv pip install pydevd"

test:
	docker exec $(CONTAINER) sh -c "cd /pptl && uv run --no-dev pytest /pptl/tests --qgis_disable_gui"

test-coverage:
	docker exec $(CONTAINER) sh -c "cd /pptl && uv run --no-dev pytest /pptl/tests \
		--qgis_disable_gui \
		--cov=/pptl/PolygonsParallelToLine/src \
		--cov-report=term-missing:skip-covered \
		--cov-report=xml:/pptl/coverage.xml \
		--junitxml=/pptl/junit.xml -o junit_family=legacy"

test-perf:
	docker exec $(CONTAINER) sh -c "cd /pptl && uv run --no-dev pytest /pptl/tests -m perf --qgis_disable_gui"

stop:
	-docker stop $(CONTAINER)

clean: stop
	-docker rm $(CONTAINER)
