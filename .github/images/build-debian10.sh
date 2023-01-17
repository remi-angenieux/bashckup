#!/usr/bin/env bash
IMAGE=remiangenieux/test-bashckup:debian10
docker build -t "$IMAGE" . -f debian10/Dockerfile
docker push "$IMAGE"