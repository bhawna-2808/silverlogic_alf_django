ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
DIR_NAME:=$(shell dirname "${ROOT_DIR}")
PROJECT_NAME:=$(shell basename "${DIR_NAME}")
CONTAINER_NAME:=${PROJECT_NAME}-$(shell basename "${ROOT_DIR}")
IMAGE_NAME:=${CONTAINER_NAME}:1.0

stop_container:
	docker stop ${CONTAINER_NAME} $^ 2>/dev/null ; true

remove_container:
	$(MAKE) stop_container
	docker rm "${CONTAINER_NAME}" $^ 2>/dev/null ; true

remove_image:
	docker image rm $(shell docker images -q "${IMAGE_NAME}" | uniq) $^ 2>/dev/null ; true

build_image:
	docker image build -t ${IMAGE_NAME} .
clean:
	$(MAKE) remove_container
	$(MAKE) remove_image

run:
	$(MAKE) remove_container
	$(MAKE) build_image

	docker run \
		--mount type=bind,source=${ROOT_DIR}/,target=/usr/src/app \
		-p 4567:4567 \
		--name ${CONTAINER_NAME} \
		${IMAGE_NAME}
