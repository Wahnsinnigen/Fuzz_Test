#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/target.elf"
LOG="$ROOT/qemu_noserial.log"
GDBPORT=3333

if [ ! -f "$BUILD" ]; then
  echo "ERROR: $BUILD not found. Run make first."
  exit 1
fi

pkill -f qemu-system-arm || true
sleep 0.2

echo "Starting QEMU (no serial). GDB port: $GDBPORT"
# start QEMU paused and with gdb stub (no serial)
qemu-system-arm -M lm3s6965evb -kernel "$BUILD" -nographic -S -gdb tcp:127.0.0.1:${GDBPORT} > "$LOG" 2>&1 &
sleep 0.5

echo "QEMU started, log: $LOG"
echo "Attach with: gdb-multiarch $BUILD"
echo "(gdb) target remote 127.0.0.1:${GDBPORT}"
ss -lntp | grep ${GDBPORT} || true

