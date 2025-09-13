.PHONY: build run test stop clean

build:
	DOCKER_SCAN_SUGGEST=false docker build -t qgis-for-pptl:ci -f Dockerfile .

# -v /pptl/.venv - an anonymous volume, which "shadows" the host's `.venv` directory
run:
	docker run -d --name qgis_pptl \
		-v "$(shell pwd):/pptl" \
		-v /pptl/.venv \
		-e PYTHONPATH=/pptl \
		qgis-for-pptl:ci

install:
	docker exec -t qgis_pptl sh -c "cd /pptl && uv venv --allow-existing --system-site-packages && uv sync --locked --no-dev"

# For an unknown reason, I need to add the pydevd package in this specific way to make the PyCharm remote debugger work with Docker
install-dev:
	docker exec -t qgis_pptl sh -c "cd /pptl && uv venv --allow-existing --system-site-packages && uv sync --locked && uv pip install pydevd"

test:
	docker exec -t qgis_pptl sh -c "cd /pptl && uv run --no-dev pytest /pptl/tests --qgis_disable_gui"

test-coverage:
	docker exec -t qgis_pptl sh -c "cd /pptl && uv run --no-dev pytest /pptl/tests \
		--qgis_disable_gui \
		--cov=/pptl \
		--cov-report=term-missing:skip-covered \
		--cov-report=xml:/pptl/coverage.xml \
		--junitxml=/pptl/junit.xml -o junit_family=legacy"

stop:
	docker stop qgis_pptl

clean: stop
	docker rm qgis_pptl
