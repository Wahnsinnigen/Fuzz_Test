#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT_DIR/target.elf"
SEED="$ROOT_DIR/inputs/seed_crash"
LOG="$ROOT_DIR/qemu_log.txt"

# build stdin harness (make target must define all-stdin)
cd "$ROOT_DIR"
echo "[run_check] Building (stdin harness)..."
make clean >/dev/null 2>&1 || true
make all-stdin

if [ ! -f "$BUILD" ]; then
  echo "[run_check] ERROR: $BUILD not found"
  exit 1
fi

mkdir -p "$(dirname "$SEED")"
if [ ! -s "$SEED" ]; then
  echo -n 'CRASHME' > "$SEED"
  echo "[run_check] created seed: $SEED"
fi

echo "[run_check] Running QEMU (stdin) and saving log to $LOG ..."
# run and save output; `|| true` so script continues even if qemu exits with nonzero
cat "$SEED" | qemu-system-arm -M lm3s6965evb -kernel "$BUILD" -nographic >"$LOG" 2>&1 || true

echo "[run_check] Done. Log saved: $LOG"
echo "[run_check] Tail of log:"
sed -n '1,200p' "$LOG" || true

