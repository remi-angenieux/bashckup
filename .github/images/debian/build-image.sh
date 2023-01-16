#!/usr/bin/env bash
IMAGE=remiangenieux/test-bashckup:debian
docker build -t "$IMAGE" .
docker push "$IMAGE"