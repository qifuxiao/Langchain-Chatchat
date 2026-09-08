#!/usr/bin/env bash
set -euo pipefail
cd /app
python docker/prepare_configs.py
# Create missing SQL tables without deleting records or calling embedding services.
python init_database.py --create-tables
case "${RUN_INIT_DB:-0}" in
    0) ;;
    1) python init_database.py --recreate-vs ;;
    *) echo 'RUN_INIT_DB must be 0 or 1' >&2; exit 1 ;;
esac
if [ "$#" -gt 0 ]; then
    exec "$@"
fi
read -r -a startup_args <<< "${STARTUP_ARGS:--a}"
if [ -n "${MODEL_NAME:-}" ]; then
    startup_args+=(-n "$MODEL_NAME")
fi
exec python startup.py "${startup_args[@]}"
