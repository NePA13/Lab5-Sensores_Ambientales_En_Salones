#!/usr/bin/env bash
set -euo pipefail

aws ecr get-login-password --region us-east-1 \
  | podman login --username AWS --password-stdin "$REGISTRY"

podman build -t "$REGISTRY/aulas-web:latest" ./web
podman push "$REGISTRY/aulas-web:latest"

podman build -t "$REGISTRY/aulas-simulador:latest" ./producer
podman push "$REGISTRY/aulas-simulador:latest"
