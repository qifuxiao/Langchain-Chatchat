#!/usr/bin/env sh
set -eu

IMAGE_TAG="${IMAGE_TAG:-langchain-chatchat-gitee:0.2.9}"
OUTPUT_DIR="${1:-dist/langchain-chatchat-gitee-0.2.9}"

if ! docker image inspect "$IMAGE_TAG" >/dev/null 2>&1; then
    echo "Image $IMAGE_TAG does not exist. Build it first with: docker compose build"
    exit 1
fi

if [ -e "$OUTPUT_DIR" ]; then
    echo "Output path already exists: $OUTPUT_DIR"
    echo "Choose a new output directory or remove it after verifying its contents."
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
docker save -o "$OUTPUT_DIR/image.tar" "$IMAGE_TAG"
cp docker-compose.offline.yml "$OUTPUT_DIR/docker-compose.yml"
cp .env.gitee.example "$OUTPUT_DIR/.env.gitee.example"
cp scripts/import-offline-bundle.sh "$OUTPUT_DIR/import-offline-bundle.sh"
chmod +x "$OUTPUT_DIR/import-offline-bundle.sh"

(
    cd "$OUTPUT_DIR"
    sha256sum image.tar docker-compose.yml .env.gitee.example import-offline-bundle.sh > SHA256SUMS
)

archive="${OUTPUT_DIR}.tar.gz"
tar -C "$(dirname "$OUTPUT_DIR")" -czf "$archive" "$(basename "$OUTPUT_DIR")"
echo "Offline bundle created: $archive"
