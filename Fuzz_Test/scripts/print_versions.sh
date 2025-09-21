#!/usr/bin/env bash
echo "=== Host info ==="
uname -a
echo
echo "=== QEMU ==="
qemu-system-arm --version 2>&1 | head -n 3
echo
echo "=== arm-none-eabi-gcc ==="
arm-none-eabi-gcc --version | head -n 1
echo
echo "=== gdb-multiarch ==="
gdb-multiarch --version 2>&1 | head -n 1
echo
echo "=== netcat ==="
nc --version 2>&1 || nc -h 2>&1 | head -n 1
echo
echo "=== Git commit ==="
git rev-parse --short HEAD || echo "(no git info)"


