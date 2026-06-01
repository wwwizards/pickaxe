# sys-tools — DESIGN.md

CREATED: 2026-06-01
MODULE: sys-tools (part of pickaxe monorepo)
PARENT: pickaxe/.HANDOFF/DESIGN.md (repo-level architecture)

---

## Purpose

sys-tools is the system observability sub-module within pickaxe. Where
etl-tools processes data files, sys-tools interrogates the local machine:
CPU, RAM, GPU utilization, power state, temperature, and driver metadata.

Its output is flat JSON — designed to pipe directly into `convert_from_json.py`
for table/CSV rendering, or accumulate to a file for time-series comparison.

---

## Architecture

### Layer 1: Probe (sys-probe.py)

Point-in-time snapshot of machine state. Each probe emits one flat JSON record:

```
{
  "timestamp": "2026-06-01T06:52:38",
  "label":     "baseline-pre-changes",
  "cpu_*":     ...,   # psutil
  "ram_*":     ...,   # psutil
  "gpu0_*":    ...,   # nvidia-smi subprocess (NVIDIA)
  "gpu1_*":    ...    # PowerShell WMI (Intel, optional --no-intel flag)
}
```

**Dependencies:**
- `psutil` — CPU + RAM (pip install psutil)
- `nvidia-smi` — NVIDIA GPU (bundled with NVIDIA drivers)
- `powershell` subprocess — Intel GPU via WMI perf counters (optional)

**Output contract:** JSON array to stdout OR append to `--output FILE`. Designed
as a pipe source for `convert_from_json.py -f - -o table`.

### Layer 2: Accumulator (probes.json)

Not a tool — a convention. Probes are labeled and appended to a shared file
(e.g., `.AI-TRAINING/probes.json`). The file grows as a time-series log of
labeled snapshots: baseline, post-tier1, post-tier2, monitor-N, etc.

Query/filter via `convert_from_json.py -q "label = post-*"`.

### Layer 3: Future — sys-diff (planned)

A `sys-diff.py` tool that reads two labeled snapshots from a probes file and
emits a diff table: field | before | after | delta | change_pct. This is the
"before/after" primitive for MVx experiment documentation.

### Layer 4: Future — sys-watch (planned)

A daemon/loop wrapper around sys-probe that emits a live terminal dashboard
(rich-based, updates in place) while also appending to the probes file.
Useful for monitoring during CuPy benchmarks or GPU stress tests.

---

## Command Design (CLI)

### sys-probe.py (v0.1.0 — current)

```
sys-probe.py [--label TEXT] [--interval N] [--count N]
             [--output FILE] [--no-intel]
```

Single-shot default (no flags) emits a one-record JSON array to stdout.

### Future: sys-diff.py (v0.2.0 target)

```
sys-diff.py --file probes.json --before LABEL_A --after LABEL_B
            [--format table|json|csv]
```

### Future: sys-watch.py (v0.3.0 target)

```
sys-watch.py [--interval N] [--output FILE] [--no-intel]
             [--columns col1,col2,...]
```

---

## Pipe Contract

sys-tools tools are pipe sources, not pipe sinks. The formatter lives in
etl-tools (`convert_from_json.py`). This separation is intentional:

```
sys-probe.py → stdout (JSON) → convert_from_json.py -f - -o table
```

sys-tools must not depend on etl-tools at import time. CLI examples may
reference the pipe pattern in docstrings, but `import` must never cross
the boundary. This keeps sys-tools independently testable and portable.

---

## Conventions

- **Probe field naming:** `{source}_{metric}_{unit}` where unit is meaningful
  (e.g., `gpu0_vram_used_mb`, `cpu_freq_mhz`, `ram_used_gb`). Unitless
  percentages use `_pct` suffix. Omit unit from boolean/string fields.
- **label:** Free-form string identifying the context of a probe. Use kebab-case.
  Convention: `{state}-{context}` e.g., `baseline-pre-changes`, `post-tier1`,
  `monitor-1`, `benchmark-cupy-warmup`.
- **--no-intel flag:** WMI perf counter query can hang (3-10s) on some systems.
  Default is to include Intel GPU; `--no-intel` skips for faster single-shot probes.
- **Python interpreter:** Use `.venv\Scripts\python.exe` from repo root. System
  Python (C:\Python314\) does NOT have psutil or numpy.
