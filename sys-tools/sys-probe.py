#!/usr/bin/env python3
# --------------------------------------------------------------------------
# MODULE: sys-probe.py
# --------------------------------------------------------------------------
# PURPOSE:
#     Capture a point-in-time system performance snapshot: CPU, RAM,
#     NVIDIA GPU (via nvidia-smi), and Intel GPU (via WMI performance
#     counters). Outputs a flat JSON record list compatible with
#     convert_from_json.py for downstream formatting and filtering.
#
# USAGE:
#     # Single snapshot to stdout (pipe to formatter)
#     python sys-probe.py | python convert_from_json.py -f - -o table
#
#     # Labeled snapshot (MVx baseline / post-change)
#     python sys-probe.py --label baseline-pre-tier1
#     python sys-probe.py --label post-tier1 --output probes.json
#
#     # Repeating monitor (every 5s, 10 samples)
#     python sys-probe.py --interval 5 --count 10 --output monitor.json
#
#     # Custom columns via formatter
#     python sys-probe.py | python convert_from_json.py -f - -o table \
#         -c timestamp,label,cpu_util_pct,gpu0_util_pct,gpu1_util_pct,ram_used_gb
#
# ARGUMENTS:
#     --label TEXT       : Tag this snapshot (default: "probe")
#     --interval N       : Seconds between snapshots in loop mode (default: 0 = single)
#     --count N          : Number of snapshots to take (default: 1)
#     --output FILE      : Append JSON records to file instead of stdout
#     --no-intel         : Skip Intel GPU WMI query (slow on some systems)
#     --format json      : Output format (json only; pipe to convert_from_json for table/csv)
#
# PIPE EXAMPLES:
#     # Table view of latest snapshot
#     python sys-probe.py | python convert_from_json.py -f - -o table
#
#     # Compare saved baselines
#     python convert_from_json.py -f probes.json -o table \
#         -c timestamp,label,cpu_util_pct,gpu0_util_pct,gpu0_vram_used_mb,gpu1_util_pct,ram_used_gb
#
#     # Filter to only post-change snapshots
#     python convert_from_json.py -f probes.json -o table -q "label = post-*"
#
# DEPENDENCIES:
#     psutil        : pip install psutil
#     nvidia-smi    : bundled with NVIDIA drivers (already present)
#     subprocess    : stdlib (Intel GPU via PowerShell WMI)
#
# LICENSE: COPYLEFT - GNU Lesser General Public License (LGPL)
# CREATED: 26-0601 BY: github.com/wwwizards
# VERSION: v0.1.0
# --------------------------------------------------------------------------

import json
import sys
import argparse
import subprocess
import os
import time
from datetime import datetime

try:
    import psutil
except ImportError:
    print("ERROR: psutil not installed. Run: pip install psutil", file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------------------
# FUNCTION: probe_cpu()
# --------------------------------------------------------------------------
def probe_cpu():
    """Capture CPU utilization, frequency, and per-core stats via psutil."""
    # cpu_percent(interval=0.5) blocks briefly for accurate reading
    util = psutil.cpu_percent(interval=0.5)
    freq = psutil.cpu_freq()
    load = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (None, None, None)
    count_logical = psutil.cpu_count(logical=True)
    count_physical = psutil.cpu_count(logical=False)

    return {
        "cpu_util_pct":       round(util, 1),
        "cpu_freq_mhz":       round(freq.current, 0) if freq else None,
        "cpu_freq_max_mhz":   round(freq.max, 0) if freq else None,
        "cpu_cores_logical":  count_logical,
        "cpu_cores_physical": count_physical,
    }


# --------------------------------------------------------------------------
# FUNCTION: probe_ram()
# --------------------------------------------------------------------------
def probe_ram():
    """Capture RAM usage via psutil."""
    mem = psutil.virtual_memory()
    return {
        "ram_used_gb":    round(mem.used  / (1024 ** 3), 2),
        "ram_total_gb":   round(mem.total / (1024 ** 3), 2),
        "ram_avail_gb":   round(mem.available / (1024 ** 3), 2),
        "ram_util_pct":   round(mem.percent, 1),
    }


# --------------------------------------------------------------------------
# FUNCTION: probe_nvidia()
# --------------------------------------------------------------------------
def probe_nvidia():
    """Capture NVIDIA GPU stats via nvidia-smi subprocess."""
    fields = [
        "name",
        "utilization.gpu",
        "utilization.memory",
        "memory.used",
        "memory.total",
        "temperature.gpu",
        "pstate",
        "driver_version",
        "compute_cap",
    ]
    query = ",".join(fields)
    try:
        result = subprocess.run(
            ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return {"gpu0_error": result.stderr.strip()}

        line = result.stdout.strip().splitlines()[0]
        parts = [p.strip() for p in line.split(",")]

        def _int(v):
            try:
                return int(v)
            except (ValueError, TypeError):
                return None

        return {
            "gpu0_name":          parts[0] if len(parts) > 0 else None,
            "gpu0_util_pct":      _int(parts[1]) if len(parts) > 1 else None,
            "gpu0_mem_util_pct":  _int(parts[2]) if len(parts) > 2 else None,
            "gpu0_vram_used_mb":  _int(parts[3]) if len(parts) > 3 else None,
            "gpu0_vram_total_mb": _int(parts[4]) if len(parts) > 4 else None,
            "gpu0_temp_c":        _int(parts[5]) if len(parts) > 5 else None,
            "gpu0_pstate":        parts[6] if len(parts) > 6 else None,
            "gpu0_driver":        parts[7] if len(parts) > 7 else None,
            "gpu0_cuda_cap":      parts[8] if len(parts) > 8 else None,
        }
    except FileNotFoundError:
        return {"gpu0_error": "nvidia-smi not found"}
    except subprocess.TimeoutExpired:
        return {"gpu0_error": "nvidia-smi timeout"}


# --------------------------------------------------------------------------
# FUNCTION: probe_intel_gpu()
# --------------------------------------------------------------------------
def probe_intel_gpu():
    """
    Capture Intel GPU utilization via Windows WMI performance counters.
    Uses PowerShell subprocess — no extra Python packages required.
    Returns gpu1_util_pct as the 3D engine utilization percentage.
    """
    ps_cmd = (
        "Get-CimInstance -Namespace root\\cimv2 "
        "-ClassName Win32_PerfFormattedCounterObject_GPUEngine "
        "-ErrorAction SilentlyContinue | "
        "Where-Object { $_.Name -like '*Intel*engtype_3D*' } | "
        "Select-Object -First 1 -ExpandProperty UtilizationPercentage"
    )
    # Fallback query using the standard GPU performance counters namespace
    ps_cmd_fallback = (
        "try { "
        "$g = Get-Counter '\\GPU Engine(*)\\Utilization Percentage' -ErrorAction Stop; "
        "$intel = $g.CounterSamples | Where-Object { $_.Path -like '*Intel*3D*' }; "
        "if ($intel) { [int]($intel | Measure-Object CookedValue -Average).Average } else { 'N/A' } "
        "} catch { 'N/A' }"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd_fallback],
            capture_output=True, text=True, timeout=15
        )
        val = result.stdout.strip()
        if val and val not in ("", "N/A"):
            try:
                return {"gpu1_util_pct": int(float(val))}
            except ValueError:
                pass
        return {"gpu1_util_pct": None}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {"gpu1_util_pct": None}


# --------------------------------------------------------------------------
# FUNCTION: take_snapshot(label, include_intel)
# --------------------------------------------------------------------------
def take_snapshot(label="probe", include_intel=True):
    """Assemble a single flat snapshot record from all probes."""
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "label":     label,
    }
    record.update(probe_cpu())
    record.update(probe_ram())
    record.update(probe_nvidia())
    if include_intel:
        record.update(probe_intel_gpu())
    else:
        record["gpu1_util_pct"] = "skipped"
    return record


# --------------------------------------------------------------------------
# FUNCTION: load_existing(path)
# --------------------------------------------------------------------------
def load_existing(path):
    """Load existing JSON array from file, return [] if missing or invalid."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
    except (json.JSONDecodeError, IOError):
        return []


# --------------------------------------------------------------------------
# FUNCTION: main()
# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="System performance probe — outputs JSON compatible with convert_from_json.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sys-probe.py | python convert_from_json.py -f - -o table
  python sys-probe.py --label baseline | python convert_from_json.py -f - -o table -c timestamp,label,cpu_util_pct,gpu0_util_pct,ram_used_gb
  python sys-probe.py --label post-tier1 --output probes.json
  python sys-probe.py --interval 5 --count 6 --label monitor --output monitor.json
        """.strip()
    )
    parser.add_argument("--label",     type=str, default="probe",
                        help="Label for this snapshot (default: probe)")
    parser.add_argument("--interval",  type=float, default=0,
                        help="Seconds between snapshots (0 = single shot, default: 0)")
    parser.add_argument("--count",     type=int, default=1,
                        help="Number of snapshots to take (default: 1, use with --interval)")
    parser.add_argument("--output",    type=str, default=None,
                        help="Append records to this JSON file instead of stdout")
    parser.add_argument("--no-intel",  action="store_true",
                        help="Skip Intel GPU WMI query (faster on systems where it hangs)")
    args = parser.parse_args()

    include_intel = not args.no_intel

    # Loop mode: --interval > 0 OR --count > 1
    loop_mode = args.interval > 0 or args.count > 1
    iterations = args.count if loop_mode else 1

    records = []
    try:
        for i in range(iterations):
            snap_label = f"{args.label}-{i+1}" if iterations > 1 else args.label
            snap = take_snapshot(label=snap_label, include_intel=include_intel)
            records.append(snap)

            if args.output:
                # Append to file incrementally (safe for long monitor runs)
                existing = load_existing(args.output)
                existing.append(snap)
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(existing, f, indent=2)
                print(f"[{snap['timestamp']}] {snap_label} → {args.output}", file=sys.stderr)
            else:
                # stdout: flush each record immediately in loop mode
                if loop_mode:
                    print(json.dumps([snap], indent=2))
                    sys.stdout.flush()

            if loop_mode and i < iterations - 1:
                time.sleep(args.interval)

    except KeyboardInterrupt:
        pass  # Ctrl-C exits cleanly in monitor mode

    # Single-shot stdout: emit full array at end (pipe-friendly)
    if not args.output and not loop_mode:
        print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
