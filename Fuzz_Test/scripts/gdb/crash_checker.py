#!/usr/bin/env python3
# scripts/gdb/crash_checker.py
#
# GDB Python helper for simple automated crash detection for QEMU+firmware.
# Usage (after connecting GDB to target):
#   (gdb) source scripts/gdb/crash_checker.py
#   (gdb) check_crash /full/path/to/seedfile
#
# Or non-interactively from the shell:
# gdb-multiarch target.elf \
#   -ex "target remote :3333" \
#   -ex "source scripts/gdb/crash_checker.py" \
#   -ex "check_crash inputs/seed_crash" \
#   -ex "quit"
#
# Adjust configuration below to match your firmware/ELF (RAM bounds, INPUT_ADDR).

import gdb
import os
import time
import json
import datetime

# ----- Configuration (edit as needed) -----
# RAM bounds (inclusive/exclusive): set to your platform's RAM area
RAM_BASE = 0x20000000
RAM_TOP  = 0x20010000

# Input address used by the firmware's memory-mapped harness
INPUT_ADDR = 0x20000100   # <- replace/confirm with your src/target.c define

# How many bytes to dump around SP for context
MEM_DUMP_BYTES = 256

# Output dir for crash reports
OUTPUT_DIR = "outputs/crashes"

# Symbol names (optional) to treat as exception handlers
HANDLER_SYMBOLS = [
    "HardFault_Handler",
    "NMI_Handler",
    "Reset_Handler",
]

# Time to wait (seconds) after continue before checking (tunable)
RUN_WAIT_SECONDS = 0.05


# ----- helper functions -----
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def now_ts():
    return datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def safe_eval(expr):
    try:
        return int(gdb.parse_and_eval(expr))
    except Exception:
        return None

def write_memory(addr_int, data_bytes):
    inf = gdb.selected_inferior()
    inf.write_memory(addr_int, data_bytes)

def read_memory(addr_int, length):
    inf = gdb.selected_inferior()
    return bytes(inf.read_memory(addr_int, length))

def dump_regs():
    regs = {}
    # typical ARM registers
    to_read = ["pc","sp","lr","r0","r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r11","r12"]
    for r in to_read:
        try:
            val = gdb.parse_and_eval("$"+r)
            regs[r] = int(val)
        except Exception:
            regs[r] = None
    return regs

def is_addr_in_ram(addr):
    return (addr is not None) and (RAM_BASE <= addr < RAM_TOP)

def find_symbol_addr(name):
    try:
        val = gdb.parse_and_eval(name)
        return int(val)
    except Exception:
        return None

# ----- crash detection logic -----
def detect_crash_condition():
    """Return (True, reason_str) if a crash is detected, else (False, None)."""
    pc = safe_eval("$pc")
    sp = safe_eval("$sp")
    if pc is None:
        return True, "cannot_read_pc"
    # obvious invalid PC (outside RAM/flash) -> probable crash
    # Note: adjust thresholds if your code runs from flash at 0x00000000
    if not (0x00000000 <= pc <= 0xFFFFFFFF):
        return True, "pc_invalid_range"
    # If PC is in RAM region but not expected (optional)
    if not is_addr_in_ram(pc):
        # allow PC in flash region too — user can refine if needed
        pass

    # Detect jump into high/low memory not part of RAM/flash heuristics
    if not is_addr_in_ram(pc) and not (0x00000000 <= pc < 0x00100000 or 0x08000000 <= pc < 0x10000000):
        return True, "pc_outside_known_regions"

    # check whether PC sits in one of the handler symbols (if resolvable)
    for sym in HANDLER_SYMBOLS:
        saddr = find_symbol_addr(sym)
        if saddr is not None and pc == saddr:
            return True, "entered_handler:"+sym

    # Check SP plausibility: must be inside RAM
    if sp is not None and not is_addr_in_ram(sp):
        return True, "sp_outside_ram"

    # No decisive crash found
    return False, None

# ----- reporting -----
def save_report(seed_path, reason, regs, mem_around_sp):
    ensure_dir(OUTPUT_DIR)
    ts = now_ts()
    pid = os.getpid()
    basename = "crash_%s_pid%d" % (ts, pid)
    outdir = os.path.join(OUTPUT_DIR, basename)
    os.makedirs(outdir, exist_ok=True)
    # save seed copy
    try:
        if seed_path and os.path.exists(seed_path):
            import shutil
            shutil.copy(seed_path, os.path.join(outdir, "seed.bin"))
    except Exception:
        pass
    # save metadata
    meta = {
        "timestamp": ts,
        "reason": reason,
        "regs": regs,
    }
    with open(os.path.join(outdir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    # save a textual register dump
    with open(os.path.join(outdir, "registers.txt"), "w") as f:
        for k,v in regs.items():
            f.write("%s: %s\n" % (k, hex(v) if v is not None else "None"))
    # save memory around SP
    if mem_around_sp is not None:
        with open(os.path.join(outdir, "mem_around_sp.bin"), "wb") as f:
            f.write(mem_around_sp)
    print("[CrashChecker] saved report to:", outdir)
    return outdir

# ----- main command implementation -----
class CrashCheckerCmd(gdb.Command):
    """check_crash <seed_file> [--addr=0x20000100] - write seed to target and run, detect crashes."""

    def __init__(self):
        super(CrashCheckerCmd, self).__init__("check_crash", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        argv = gdb.string_to_argv(arg)
        if len(argv) < 1:
            print("Usage: check_crash /full/path/to/seedfile [--addr=0x...]")
            return
        seed_path = argv[0]
        addr = INPUT_ADDR
        for a in argv[1:]:
            if a.startswith("--addr="):
                try:
                    addr = int(a.split("=",1)[1], 0)
                except Exception:
                    pass

        # ensure an inferior exists/connected
        try:
            inf = gdb.selected_inferior()
        except Exception as e:
            print("[CrashChecker] No inferior selected/connected:", e)
            return

        # read seed
        if not os.path.exists(seed_path):
            print("[CrashChecker] seed not found:", seed_path)
            return
        with open(seed_path, "rb") as f:
            seed = f.read()

        try:
            # write seed into target memory
            print("[CrashChecker] Writing seed (%d bytes) to 0x%x" % (len(seed), addr))
            write_memory(addr, seed)
        except Exception as e:
            print("[CrashChecker] write_memory failed:", e)
            return

        # optionally reset the system to ensure deterministic start
        try:
            print("[CrashChecker] Resetting target (monitor system_reset)")
            gdb.execute("monitor system_reset")
        except Exception:
            # fallback: try 'monitor reset' or ignore
            try:
                gdb.execute("monitor reset")
                print("[CrashChecker] monitor reset used")
            except Exception:
                print("[CrashChecker] reset failed or not supported")

        # let it run for a short while
        try:
            gdb.execute("continue")
        except Exception:
            # sometimes it's already running; ignore
            pass

        # small wait to allow instructions to execute
        time.sleep(RUN_WAIT_SECONDS)

        # stop the target to inspect (if possible)
        try:
            gdb.execute("interrupt")
        except Exception:
            pass

        # read registers and detect crash
        regs = dump_regs()
        crashed, reason = detect_crash_condition()

        # if crash, dump memory around SP
        memdump = None
        sp = regs.get("sp", None)
        if crashed:
            if sp is not None and is_addr_in_ram(sp):
                start = max(RAM_BASE, sp - MEM_DUMP_BYTES//2)
                length = MEM_DUMP_BYTES
                try:
                    memdump = read_memory(start, length)
                except Exception:
                    memdump = None
            outdir = save_report(seed_path, reason, regs, memdump)
            # optionally leave GDB/QEMU stopped for inspection
            print("[CrashChecker] possible crash detected:", reason)
        else:
            print("[CrashChecker] No crash detected (reason None).")
            # optional: still save a brief run log
            #save_report(seed_path, "no_crash", regs, None)

CrashCheckerCmd()
print("[CrashChecker] loaded. Use 'check_crash /path/to/seed [--addr=0x...]'")


