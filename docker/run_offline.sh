#!/usr/bin/env bash
# Run on the deployment host; model API endpoints must be reachable.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${IMAGE:-langchain-chatchat:offline}"
CONTAINER_NAME="${CONTAINER_NAME:-chatchat}"
DATA_DIR="${DATA_DIR:-$ROOT_DIR/dist/data}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"
KB_VOLUME="${KB_VOLUME:-${CONTAINER_NAME}-knowledge-base}"

docker image inspect "$IMAGE" >/dev/null
if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
    echo "Container $CONTAINER_NAME already exists. Use docker start/stop; explicitly remove it only after checking its mounts." >&2
    exit 1
fi
if [ ! -f "$ENV_FILE" ]; then
    echo "Create $ENV_FILE using docker/api.env.example before starting." >&2
    exit 1
fi
mkdir -p "$DATA_DIR/logs"
# A new named volume is seeded from image data; it survives container deletion.
VOLUMES=(-v "${DATA_DIR}/logs:/app/logs")
if [ "${MOUNT_KB:-0}" = "1" ]; then
    if [ ! -d "$DATA_DIR/knowledge_base" ]; then
        echo "Prepare $DATA_DIR/knowledge_base before using MOUNT_KB=1." >&2
        exit 1
    fi
    VOLUMES+=(-v "${DATA_DIR}/knowledge_base:/app/knowledge_base")
else
    VOLUMES+=(-v "${KB_VOLUME}:/app/knowledge_base")
fi
docker run -d \
    --name "$CONTAINER_NAME" --restart unless-stopped \
    -p "${WEBUI_PORT:-8501}:8501" -p "${API_PORT:-7861}:7861" \
    "${VOLUMES[@]}" --env-file "$ENV_FILE" \
    -e RUN_INIT_DB="${RUN_INIT_DB:-0}" \
    -e STARTUP_ARGS="${STARTUP_ARGS:--a}" \
    -e MODEL_NAME="${MODEL_NAME:-}" \
    "$IMAGE"
echo "View logs: docker logs -f $CONTAINER_NAME"
