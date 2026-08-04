#!/bin/sh
set -eu

# Runtime configuration is intentionally generated inside the container.  The
# examples read GITEE_AI_* variables, so no API key is baked into the image.
for template in /app/configs/*.py.example; do
    target="${template%.example}"
    if [ ! -f "$target" ]; then
        cp "$template" "$target"
    fi
done

if [ ! -f /app/configs/__init__.py ]; then
    echo "Missing required configs/__init__.py in image" >&2
    exit 1
fi

exec "$@"
