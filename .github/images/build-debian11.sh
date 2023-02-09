#!/usr/bin/env bash
IMAGE=remiangenieux/test-bashckup:debian11
docker build -t "$IMAGE" . -f debian11/Dockerfile
docker push "$IMAGE"