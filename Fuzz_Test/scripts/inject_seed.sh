#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SEED="$ROOT_DIR/inputs/seed_crash"
HOST="127.0.0.1"
PORT=4444

if [ ! -f "$SEED" ]; then
  echo "[inject_seed] ERROR: seed not found: $SEED"
  exit 1
fi

echo "[inject_seed] Sending seed to ${HOST}:${PORT} ..."
# use netcat (openbsd netcat / nc)
printf '%s' "$(cat "$SEED")" | nc "$HOST" "$PORT"
echo
echo "[inject_seed] Done."

