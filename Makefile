.PHONY: build run test stop clean

# Build the Docker image
build:
	docker build -t qgis-for-pptl:ci -f Dockerfile .

# Run the Docker container
run:
	docker run -d --name qgis_pptl \
		-v "$(shell pwd):/pptl" \
		-e PYTHONPATH=/pptl \
		-e PPTL_TEST=1 \
		qgis-for-pptl:ci \
		tail -f /dev/null

# Run tests in the container
test:
	docker exec -t qgis_pptl sh -c "pytest /pptl/tests --qgis_disable_gui"

# Stop the container
stop:
	docker stop qgis_pptl

# Remove the container
clean: stop
	docker rm qgis_pptl
