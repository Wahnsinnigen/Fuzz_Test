#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/target.elf"
LOG="$ROOT/qemu_withserial.log"
GDBPORT=3333
SERPORT=4444

if [ ! -f "$BUILD" ]; then
  echo "ERROR: $BUILD not found. Run make first."
  exit 1
fi

pkill -f qemu-system-arm || true
sleep 0.2

echo "Starting QEMU (gdb + serial). GDB:$GDBPORT Serial:$SERPORT"
nohup qemu-system-arm -M lm3s6965evb -kernel "$BUILD" -nographic -S -gdb tcp:127.0.0.1:${GDBPORT} -serial tcp:127.0.0.1:${SERPORT},server > "$LOG" 2>&1 &
sleep 0.6

echo "QEMU started (background). Log: $LOG"
echo "Attach GDB:"
echo "  gdb-multiarch $BUILD"
echo "  (gdb) target remote 127.0.0.1:${GDBPORT}"
echo "To inject seed (in a third terminal):"
echo "  printf 'CRASHME' | nc 127.0.0.1 ${SERPORT}"
ss -lntp | egrep "${GDBPORT}|${SERPORT}" || true
tail -n 30 "$LOG" || true

