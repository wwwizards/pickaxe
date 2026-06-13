#!/usr/bin/env python3
# --------------------------------------------------------------------------
# MODULE: gpu-bench.py
# --------------------------------------------------------------------------
# PURPOSE:
#     Benchmark GPU vs CPU matrix multiplication (GEMM) using CuPy and numpy.
#     Quantifies speedup of NVIDIA CUDA compute over numpy on the same data.
#     Designed as a companion to sys-probe.py in the pickaxe sys-tools suite.
#
# USAGE:
#     # Quick benchmark (default 2048x2048 float32 GEMM)
#     python gpu-bench.py
#
#     # Custom matrix size
#     python gpu-bench.py --size 4096
#
#     # Multiple timed runs (averaged)
#     python gpu-bench.py --runs 5
#
#     # GPU-only (skip numpy baseline)
#     python gpu-bench.py --no-cpu
#
#     # JSON output (pipe-friendly)
#     python gpu-bench.py --json
#     python gpu-bench.py --json | python etl-tools/convert_from_json.py -f - -o table
#
# REQUIREMENTS:
#     cupy-cuda12x          : pip install cupy-cuda12x
#     nvidia-cublas-cu12    : pip install nvidia-cublas-cu12
#     nvidia-cuda-runtime-cu12 : pip install nvidia-cuda-runtime-cu12
#     nvidia-cuda-nvrtc-cu12: pip install nvidia-cuda-nvrtc-cu12
#     numpy                 : pip install numpy
#
# NOTES:
#     - curand is NOT required (data generated with numpy, transferred via cp.asarray)
#     - Requires TdrDelay >= 10 in HKLM\SYSTEM\...\GraphicsDrivers on WDDM systems
#       (default 2s kills CUDA context on first init from P8 sleep state)
#     - CUDA 13 dropped Pascal (sm_61) — must use cupy-cuda12x for Quadro P520 and peers
#     - Warm-up run is always performed before timing to ensure GPU is awake
#
# LICENSE: COPYLEFT - GNU Lesser General Public License (LGPL)
# CREATED: 2026-06-01 BY: github.com/wwwizards
# VERSION: v0.1.0
# --------------------------------------------------------------------------

import argparse
import json
import sys
import time


def parse_args():
    p = argparse.ArgumentParser(
        description='GPU vs CPU GEMM benchmark (CuPy vs numpy)'
    )
    p.add_argument('--size', type=int, default=2048,
                   help='Matrix dimension N for N×N float32 GEMM (default: 2048)')
    p.add_argument('--runs', type=int, default=1,
                   help='Number of timed runs to average (default: 1)')
    p.add_argument('--warmup', type=int, default=1,
                   help='Number of warmup runs before timing (default: 1)')
    p.add_argument('--no-cpu', action='store_true',
                   help='Skip numpy CPU baseline')
    p.add_argument('--json', action='store_true',
                   help='Output results as JSON (pipe to convert_from_json.py)')
    return p.parse_args()


def run_cpu_bench(A_np, B_np, runs):
    import numpy as np
    # warmup
    _ = np.matmul(A_np, B_np)
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        np.matmul(A_np, B_np)
        times.append((time.perf_counter() - t0) * 1000)
    return sum(times) / len(times)


def run_gpu_bench(A_np, B_np, warmup, runs):
    try:
        import cupy as cp
    except ImportError as e:
        print(f'ERROR: CuPy not available — {e}', file=sys.stderr)
        print('Install: pip install cupy-cuda12x nvidia-cublas-cu12 nvidia-cuda-runtime-cu12 nvidia-cuda-nvrtc-cu12', file=sys.stderr)
        sys.exit(1)

    # Transfer to GPU (use np.random data to avoid curand requirement)
    A_cp = cp.asarray(A_np)
    B_cp = cp.asarray(B_np)

    # Warmup
    for _ in range(warmup):
        _ = cp.matmul(A_cp, B_cp)
        cp.cuda.Stream.null.synchronize()

    # Timed runs
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        cp.matmul(A_cp, B_cp)
        cp.cuda.Stream.null.synchronize()
        times.append((time.perf_counter() - t0) * 1000)

    # Device name (best-effort)
    try:
        device_name = cp.cuda.runtime.getDeviceProperties(0).get('name', b'unknown')
        if isinstance(device_name, bytes):
            device_name = device_name.decode('utf-8', errors='replace')
    except Exception:
        device_name = 'unknown'

    vram_used_mb = 0
    try:
        mem = cp.cuda.Device(0).mem_info
        total_mb = mem[1] / 1024 / 1024
        free_mb = mem[0] / 1024 / 1024
        vram_used_mb = round(total_mb - free_mb, 1)
    except Exception:
        pass

    return sum(times) / len(times), device_name, vram_used_mb


def main():
    args = parse_args()
    import numpy as np

    N = args.size
    A_np = np.random.rand(N, N).astype(np.float32)
    B_np = np.random.rand(N, N).astype(np.float32)

    gpu_ms, device_name, vram_used_mb = run_gpu_bench(A_np, B_np, args.warmup, args.runs)
    cpu_ms = run_cpu_bench(A_np, B_np, args.runs) if not args.no_cpu else None

    speedup = (cpu_ms / gpu_ms) if cpu_ms is not None else None

    if args.json:
        record = {
            'tool': 'gpu-bench',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'matrix_size': N,
            'runs': args.runs,
            'gpu_device': device_name,
            'gpu_ms': round(gpu_ms, 2),
            'cpu_ms': round(cpu_ms, 2) if cpu_ms is not None else None,
            'speedup': round(speedup, 2) if speedup is not None else None,
            'vram_used_mb': vram_used_mb,
        }
        print(json.dumps(record))
    else:
        print(f'matrix : {N}x{N} float32 GEMM  ({args.runs} run{"s" if args.runs > 1 else ""} averaged)')
        print(f'device : {device_name}')
        if cpu_ms is not None:
            print(f'numpy  (CPU) : {cpu_ms:.2f} ms')
        print(f'cupy   (GPU) : {gpu_ms:.2f} ms')
        if speedup is not None:
            marker = ' ✅' if speedup >= 2.0 else ' (< 2x — transfer overhead likely dominant)'
            print(f'speedup      : {speedup:.1f}x{marker}')
        if vram_used_mb:
            print(f'VRAM used    : {vram_used_mb:.0f} MB')


if __name__ == '__main__':
    main()
