#!/usr/bin/env bash
set -e
OLD_PWD=$(pwd)
cd "$(dirname "$0")"

# Build docker image
IMAGE=remiangenieux/test-bashckup:debian
CONTAINER_NAME=test-bashckup
docker build -t "$IMAGE" ./images/debian
docker push "$IMAGE"

# Create container
docker run -d --name "$CONTAINER_NAME" "$IMAGE" /usr/bin/tail -f /dev/null
docker cp ../. "$CONTAINER_NAME":/opt
set +e

# RUN TESTS
docker exec -w /opt -t "$CONTAINER_NAME" /bin/bash -c "service mariadb start && service rsync start && pip install .[tests] && pytest -s"
TEST_RESULTS=$?

# AFTER TESTS
#docker container rm --force "$CONTAINER_NAME"
cd "$OLD_PWD"

# EXIT
exit $TEST_RESULTS