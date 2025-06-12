.PHONY: build run test stop clean

build:
	docker build -t qgis-for-pptl:ci -f Dockerfile .

run:
	docker run -d --name qgis_pptl \
		-v "$(shell pwd):/pptl" \
		-e PYTHONPATH=/pptl \
		qgis-for-pptl:ci

install-ci:
	docker exec -t qgis_pptl sh -c "cd /pptl && poetry install --only ci"

# For an unknown reason, I need to add the pydevd package in this specific way to make the PyCharm remote debugger work
install-local:
	docker exec -t qgis_pptl sh -c "cd /pptl && poetry install && poetry add pydevd"

test:
	docker exec -t qgis_pptl sh -c "cd /pptl && poetry run pytest /pptl/tests --qgis_disable_gui"


test-coverage:
	docker exec -t qgis_pptl sh -c "cd /pptl && poetry run pytest /pptl/tests \
		--qgis_disable_gui \
		--cov=/pptl \
		--cov-report=term-missing:skip-covered \
		--cov-report=xml:/pptl/coverage.xml \
		--junitxml=/pptl/junit.xml -o junit_family=legacy"

stop:
	docker stop qgis_pptl

clean: stop
	docker rm qgis_pptl
