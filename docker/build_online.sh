#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
IMAGE="${IMAGE:-langchain-chatchat:offline}"
docker build \
    --build-arg TORCH_CPU_INDEX="${TORCH_CPU_INDEX:-https://download.pytorch.org/whl/cpu}" \
    -t "$IMAGE" .
docker image inspect --format '{{.Os}}/{{.Architecture}} {{.Size}} bytes' "$IMAGE"
echo "Export: GZIP=1 bash docker/export_image.sh"
