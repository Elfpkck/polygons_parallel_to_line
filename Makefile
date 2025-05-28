.PHONY: build run test stop clean

build:
	docker build -t qgis-for-pptl:ci -f Dockerfile .

run:
	docker run -d --name qgis_pptl \
		-v "$(shell pwd):/pptl" \
		-e PYTHONPATH=/pptl \
		-e PPTL_TEST=1 \
		qgis-for-pptl:ci \
		tail -f /dev/null

test:
	docker exec -t qgis_pptl sh -c "pytest /pptl/tests --qgis_disable_gui"

test-coverage:
	docker exec -t qgis_pptl sh -c "pytest /pptl/tests --qgis_disable_gui --cov=pptl --cov-branch --cov-report=term-missing:skip-covered --cov-report=xml:/pptl/coverage.xml"

stop:
	docker stop qgis_pptl

clean: stop
	docker rm qgis_pptl
