# Reproduce steps (minimal)

Environment:
- Ubuntu XX.XX (virtualbox), QEMU 9.1.1, arm-none-eabi-gcc 13.x, gdb-multiarch
- Python 3.8+ (for the GDB controller script in `scripts/gdb/crash_checker.py`; optional `pygdbmi` if you prefer a wrapper)

1) Build (stdin harness)
$ make clean && make all-stdin

2) Prepare input
$ echo -n 'CRASHME' > inputs/seed_crash

3) Run reproduction (uses stdin harness)
$ ./scripts/run_check.sh
Note: `scripts/run_check.sh` is a quick stdin smoke test (no GDB). It does not use
 `scripts/gdb/crash_checker.py` and does not save crash artefacts.

### Automated crash detection via GDB scripting

Start QEMU first (canonical GDB-only flow):
./scripts/start_qemu_no_serial.sh

Open a second terminal and run the controller explicitly:
gdb-multiarch target.elf \
  -ex "target remote 127.0.0.1:3333" \
  -ex "source scripts/gdb/crash_checker.py" \
  -ex "check_crash inputs/seed_crash" \
  -ex "quit"

### The Python controller writes the testcase to INPUT_ADDR, issues `monitor system_reset`,
### and detects HardFault/illegal instruction/PC anomalies/timeout.
### On detection it saves artefacts under `outputs/crashes/`.


4) Inspect QEMU log:
$ sed -n '1,200p' qemu_log.txt

5) Debugging with GDB (symbolic)
# in terminal A:
$ ./scripts/start_qemu_no_serial.sh   # starts qemu with -gdb tcp::3333 (CPU halted -S)
# in terminal B:
$ gdb-multiarch target.elf
(gdb) target remote 127.0.0.1:3333
(gdb) break reset_handler
(gdb) continue

=== Host info ===
Linux xsy-VirtualBox 6.11.0-25-generic #25~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Tue Apr 15 17:20:50 UTC 2 x86_64 x86_64 x86_64 GNU/Linux

=== QEMU ===
QEMU emulator version 9.1.1
Copyright (c) 2003-2024 Fabrice Bellard and the QEMU Project developers

=== arm-none-eabi-gcc ===
arm-none-eabi-gcc (15:13.2.rel1-2) 13.2.1 20231009

=== gdb-multiarch ===
GNU gdb (Ubuntu 15.0.50.20240403-0ubuntu1) 15.0.50.20240403-git

=== netcat ===
nc: invalid option -- '-'
usage: nc [-46CDdFhklNnrStUuvZz] [-I length] [-i interval] [-M ttl]
	  [-m minttl] [-O length] [-P proxy_username] [-p source_port]
	  [-q seconds] [-s sourceaddr] [-T keyword] [-V rtable] [-W recvlimit]
	  [-w timeout] [-X proxy_protocol] [-x proxy_address[:port]]
	  [destination] [port]
OpenBSD netcat (Debian patchlevel 1.226-1ubuntu2)


### Diagnostics: serial + GDB binding issue (optional)

On the test host, we observed that running QEMU with both `-gdb tcp::3333` and `-serial tcp::4444,server` can exhibit host-dependent binding behaviour: the serial socket may bind successfully while the GDB TCP port fails to accept connections (or vice versa). To provide diagnostic evidence, a system-call trace was captured with `strace` and relevant socket calls were extracted.

Command used to capture diagnostic trace:

sudo strace -f -s 200 -o docs/qemu_strace.log \
  qemu-system-arm -M lm3s6965evb -kernel target.elf -nographic -S -gdb tcp::3333 -serial tcp::4444,server

Relevant excerpt saved in: `docs/qemu_strace_sockets.txt`.

Interpretation: see `docs/qemu_strace_sockets.txt`. If `bind(...)=0` and `listen(...)=0` are present for the serial port but `connect(...)=...` or `bind(...)= -1 EADDRINUSE` appears for the GDB port, this indicates a host-level port conflict or ordering issue. For reproducible experiments in the paper we therefore used the canonical GDB-only flow (`-gdb tcp::3333` without `-serial tcp::4444,server`) unless interactive serial injection was explicitly required.


