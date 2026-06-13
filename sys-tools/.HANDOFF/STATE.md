# sys-tools — STATE.md

## Snapshot

- Project: sys-tools (pickaxe sub-module)
- Date: 2026-06-01
- Phase: v0.1.0 — sys-probe.py (initial release)
- Status: active

---

## What shipped in this session (2026-06-01)

- `sys-probe.py` v0.1.0 — point-in-time snapshot: CPU (psutil), RAM (psutil),
  NVIDIA GPU (nvidia-smi), Intel GPU (PowerShell WMI, optional)
- Outputs flat JSON array to stdout or appends to `--output FILE`
- `--label`, `--interval`, `--count`, `--no-intel` flags
- Pipe-compatible with `etl-tools/convert_from_json.py -f - -o table`
- Moved from `etl-tools/` to `sys-tools/` for independent evolution
- `.HANDOFF/` scaffolded: DESIGN.md, STATE.md, ROADMAP.md
- Baseline probe captured: `.AI-TRAINING/probes.json` (label: baseline-pre-changes)
- GPU optimization MVx documented: `.AI-TRAINING/mvsx-stories/260601-GPU-Utilization-Optimization.md`

---

## Open items

- [ ] Post-Tier-1 probe pending (after Windows Graphics pref applied for Code.exe)
- [ ] Post-Tier-2 probe pending (after `pip install cupy-cuda13x`)
- [ ] numpy timing baseline pending (before CuPy install)
- [ ] CuPy timing benchmark pending
- [ ] Intel GPU WMI query needs validation on this machine (currently using `--no-intel`)
- [ ] `sys-diff.py` not yet built (v0.2.0 target — see ROADMAP.md)

---

## Current Python environment note

`psutil` is installed in `.venv` at repo root (`C:\PROJECTS\LogicWizards\.venv`).
System Python 3.14 (`C:\Python314\`) does NOT have psutil. Always use:

```powershell
C:\PROJECTS\LogicWizards\.venv\Scripts\python.exe sys-tools\sys-probe.py
# or activate venv first:
& C:\PROJECTS\LogicWizards\.venv\Scripts\Activate.ps1
python sys-tools\sys-probe.py
```

---

## Baseline data (pre-GPU optimization changes)

Captured 2026-06-01T06:52:38 on ThinkPad (i7-11850H, Quadro P520, 40GB RAM):

| metric | value |
|---|---|
| cpu_util_pct | 19.1% |
| cpu_freq_mhz | 804 MHz |
| ram_used_gb | 17.98 / 39.76 GB |
| gpu0_util_pct | 0% |
| gpu0_vram_used_mb | 0 MB |
| gpu0_temp_c | 44°C |
| gpu0_pstate | P8 (deep sleep) |
| gpu0_driver | 582.08 |
| gpu0_cuda_cap | 6.1 |
