# sys-tools

System observability tools. Part of the [pickaxe](../README.md) monorepo.

Interrogates the local machine — CPU, RAM, NVIDIA GPU, Intel GPU — and emits
flat JSON snapshots. The probe source half of the pickaxe pipeline: pipe its
output into `etl-tools/convert_from_json.py` for table/CSV rendering, or
accumulate to a file for time-series and before/after comparison.

---

## Requirements

```powershell
# psutil — the only third-party dep
pip install psutil

# nvidia-smi must be on PATH (ships with NVIDIA drivers)
nvidia-smi --version

# powershell on PATH for Intel GPU queries (Windows only, optional)
# Use --no-intel to skip if WMI is unavailable or slow
```

---

## Quick start

```powershell
# Single snapshot to stdout
.venv\Scripts\python.exe sys-tools\sys-probe.py --label "baseline"

# Append to accumulator file (creates if missing)
.venv\Scripts\python.exe sys-tools\sys-probe.py --label "baseline" `
  --output .AI-TRAINING\probes.json

# Skip slow Intel GPU query
.venv\Scripts\python.exe sys-tools\sys-probe.py --label "baseline" --no-intel

# Monitor loop: 10 samples, 30 seconds apart
.venv\Scripts\python.exe sys-tools\sys-probe.py --label "under-load" `
  --interval 30 --count 10 --no-intel --output .AI-TRAINING\probes.json
```

---

## CLI reference

```
sys-probe.py [--label TEXT] [--interval N] [--count N]
             [--output FILE] [--no-intel]

  --label TEXT    Tag for this snapshot (default: "probe")
  --interval N    Seconds between probes in loop mode (default: 5)
  --count N       Number of probes to take in loop mode (default: 1)
  --output FILE   Append JSON record(s) to this file (accumulator pattern)
  --no-intel      Skip Intel GPU WMI query (faster, use when Intel data not needed)
```

---

## gpu-bench.py — CuPy vs numpy GEMM Benchmark

Benchmarks GPU (CuPy) vs CPU (numpy) matrix multiplication to quantify
CUDA compute speedup. Born from the June 2026 GPU optimization experiment.

```powershell
# Quick benchmark (default 2048x2048 float32)
.venv\Scripts\python.exe sys-tools\gpu-bench.py

# Larger matrix, 3 averaged runs
.venv\Scripts\python.exe sys-tools\gpu-bench.py --size 4096 --runs 3

# JSON output (pipe-friendly)
.venv\Scripts\python.exe sys-tools\gpu-bench.py --json
```

Requires: `pip install cupy-cuda12x nvidia-cublas-cu12 nvidia-cuda-runtime-cu12 nvidia-cuda-nvrtc-cu12`
Note: data generation uses numpy + `cp.asarray()` — `nvidia-curand-cu12` is NOT required.

```
gpu-bench.py [--size N] [--runs N] [--warmup N] [--no-cpu] [--json]

  --size N      Matrix dimension for NxN float32 GEMM (default: 2048)
  --runs N      Timed runs to average (default: 1)
  --warmup N    Warmup runs before timing (default: 1)
  --no-cpu      Skip numpy CPU baseline
  --json        Emit single JSON record (pipe to convert_from_json.py)
```

---

## probes-chart.py — Probe Comparison Bar Chart

Reads a `probes.json` accumulator and generates a 2×3 bar chart comparing
CPU, RAM, GPU utilization, temperature, and frequency across all probes.
The visual companion to `sys-probe.py`. Regenerate after any new probe.

```powershell
# Default paths (probes.json + mvsx-stories chart)
.venv\Scripts\python.exe sys-tools\probes-chart.py

# Explicit paths
.venv\Scripts\python.exe sys-tools\probes-chart.py `
  --input .AI-TRAINING\probes.json `
  --output .AI-TRAINING\mvsx-stories\my-chart.png

# Custom title
.venv\Scripts\python.exe sys-tools\probes-chart.py --title "My GPU R&D Session"
```

Requires: `pip install matplotlib numpy`

```
probes-chart.py [--input FILE] [--output FILE] [--title TEXT]

  --input  FILE   Path to probes JSON array (default: .AI-TRAINING/probes.json)
  --output FILE   Output PNG path
  --title  TEXT   Chart title
```

---

Each probe is one flat JSON record:

```json
{
  "timestamp":        "2026-06-01T06:52:38",
  "label":            "baseline",
  "cpu_util_pct":     19.1,
  "cpu_freq_mhz":     804,
  "cpu_core_count":   16,
  "ram_total_gb":     39.76,
  "ram_used_gb":      17.98,
  "ram_util_pct":     45.2,
  "gpu0_name":        "Quadro P520",
  "gpu0_util_pct":    0,
  "gpu0_vram_used_mb": 0,
  "gpu0_vram_total_mb": 2048,
  "gpu0_temp_c":      44,
  "gpu0_pstate":      "P8",
  "gpu0_driver":      "582.08",
  "intel_gpu_util_pct": null
}
```

`--output FILE` writes a JSON array (`[{...}, {...}]`), appending each run.
Stdout always emits a single-record array (pipe-compatible with `convert_from_json.py -f -`).

---

## Pipeline usage

Pipe a single probe into the formatter for an instant table:

```powershell
.venv\Scripts\python.exe sys-tools\sys-probe.py --label "post-tier1" --no-intel `
  | .venv\Scripts\python.exe etl-tools\convert_from_json.py -f - -o table `
  -c "timestamp,label,cpu_util_pct,gpu0_util_pct,gpu0_vram_used_mb,gpu0_temp_c,gpu0_pstate"
```

Render the full accumulated probes file:

```powershell
.venv\Scripts\python.exe etl-tools\convert_from_json.py `
  -f .AI-TRAINING\probes.json -o table `
  -c "timestamp,label,cpu_util_pct,gpu0_util_pct,gpu0_temp_c,gpu0_pstate,ram_util_pct"
```

---

## MVx experiment workflow

sys-probe is designed for hypothesis-driven measurement. Capture named snapshots
before and after a change, then compare:

```powershell
# 1. Baseline (before any changes)
.venv\Scripts\python.exe sys-tools\sys-probe.py --label "baseline" `
  --no-intel --output .AI-TRAINING\probes.json

# 2. Apply change (e.g. Windows GPU preference, CuPy install)

# 3. Capture post-change probe
.venv\Scripts\python.exe sys-tools\sys-probe.py --label "post-tier1" `
  --no-intel --output .AI-TRAINING\probes.json

# 4. Compare side-by-side
.venv\Scripts\python.exe etl-tools\convert_from_json.py `
  -f .AI-TRAINING\probes.json -o table `
  -c "timestamp,label,gpu0_util_pct,gpu0_pstate,gpu0_temp_c,cpu_util_pct"
```

See `.AI-TRAINING/mvsx-stories/260601-GPU-Utilization-Optimization.md` for a
live example with NVIDIA Quadro P520 baseline data.

---

## Files

| File | Purpose |
|---|---|
| `sys-probe.py` | Main tool — v0.1.0 |
| `.HANDOFF/DESIGN.md` | Architecture, layer model, pipe contract, field conventions |
| `.HANDOFF/STATE.md` | Current version, what shipped, open items, baseline data |
| `.HANDOFF/ROADMAP.md` | v0.2.0 sys-diff → v0.3.0 sys-watch → v0.4.0 sys-report |
