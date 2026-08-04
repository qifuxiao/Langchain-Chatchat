#!/usr/bin/env sh
set -eu

ARCHIVE="${1:?Usage: $0 /path/to/langchain-chatchat-gitee-0.2.9.tar.gz [target-directory]}"
TARGET_DIR="${2:-./langchain-chatchat-gitee-offline}"

if [ -e "$TARGET_DIR" ]; then
    echo "Target path already exists: $TARGET_DIR"
    exit 1
fi

mkdir -p "$TARGET_DIR"
tar -xzf "$ARCHIVE" -C "$TARGET_DIR" --strip-components=1
(
    cd "$TARGET_DIR"
    sha256sum -c SHA256SUMS
)
docker load -i "$TARGET_DIR/image.tar"
cp "$TARGET_DIR/.env.gitee.example" "$TARGET_DIR/.env"

echo "Image loaded and deployment files extracted to: $TARGET_DIR"
echo "Edit $TARGET_DIR/.env before starting the service."
echo "Start with: cd $TARGET_DIR && docker compose up -d"
