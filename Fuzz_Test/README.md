# QEMU Cortex-M Crash Detection (Thesis Artefacts)

This repository contains the **minimal firmware, scripts, and documentation** used in the thesis to:
- build a small ARM Cortex-M (LM3S6965EVB) firmware,
- run it under QEMU with a **GDB stub**,
- **automatically detect crashes** via a Python GDB controller, and
- **save & replay** crash artefacts for reproducibility.

> **Canonical flow:** QEMU + **GDB-only** (no serial server).  
> **Experimental:** Serial injection exists for interactive use but is **not** used for evidence.

---

## Snapshot used in the thesis

- **Commit:** `<COMMIT-SHA>`
- **Tag:** `v1.0-thesis`

```bash
git fetch --all --tags
git checkout <COMMIT-SHA>    # or: git checkout v1.0-thesis

