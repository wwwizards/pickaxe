#------------------------------------------------------------------------------
# SCRIPT: probes-chart.py
#------------------------------------------------------------------------------
#  PURPOSE: Generate a comparison bar chart from sys-probe.py snapshots
# ABSTRACT: Reads a probes JSON file (array of flat probe records), plots key
#           metrics side-by-side across all probes, and saves a PNG chart.
#           Designed to complement sys-probe.py and convert_from_json.py.
# REQUIRES: matplotlib, numpy (pip install matplotlib numpy)
#  CREATED: 2026-06-01 BY: Joe Negron <Joe@LogicWizards.NYC>
#  COMPANY: LogicWizards.NYC <LogicWizards.NYC>
#  VERSION: 0.1.0
#  LICENSE: MIT
#  USAGE:
#     python probes-chart.py
#     python probes-chart.py --input .AI-TRAINING\probes.json
#     python probes-chart.py --input probes.json --output chart.png
#------------------------------------------------------------------------------

import argparse
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

DEFAULT_INPUT = os.path.join(
    os.path.dirname(__file__),
    '..', '..', '..', '..', '..', '.AI-TRAINING', 'probes.json'
)
DEFAULT_OUTPUT = os.path.join(
    os.path.dirname(__file__),
    '..', '..', '..', '..', '..', '.AI-TRAINING', 'mvsx-stories',
    '60601-GPU-Utilization-Optimization-Image-ComparisonChart.png'
)

LABEL_ALIASES = {
    'baseline-pre-changes':    'baseline',
    'post-tier1-gpu-pref':     'post-tier1',
    'pre-tdrdelay-reboot':     'pre-tdr\nreboot',
    'post-tier2-tdrdelay-cupy': 'post-tier2\n(TdrDelay+CuPy)',
}

METRICS = [
    ('cpu_util_pct',  'CPU Utilization',          '%'  ),
    ('ram_util_pct',  'RAM Utilization',           '%'  ),
    ('ram_used_gb',   'RAM Used',                  'GB' ),
    ('gpu0_util_pct', 'GPU-0 Utilization (P520)',  '%'  ),
    ('gpu0_temp_c',   'GPU-0 Temperature',         'C'  ),
    ('cpu_freq_mhz',  'CPU Frequency',             'MHz'),
]

COLORS = ['#4C72B0', '#DD8452', '#55A868', '#C44E52',
          '#8172B2', '#937860', '#DA8BC3', '#8C8C8C']


def load_probes(path):
    with open(path, encoding='utf-8') as f:
        raw = f.read().strip()
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        return [json.loads(line) for line in raw.splitlines() if line.strip()]


def short_label(label):
    return LABEL_ALIASES.get(label, label.replace('-', '\n'))


def main():
    parser = argparse.ArgumentParser(description='Generate probe comparison chart')
    parser.add_argument('--input',  default=DEFAULT_INPUT,  help='Path to probes.json')
    parser.add_argument('--output', default=DEFAULT_OUTPUT, help='Output PNG path')
    parser.add_argument('--title',  default='System Probe Comparison - LogicWizards GPU R&D (2026-06-01)',
                        help='Chart title')
    args = parser.parse_args()

    input_path  = os.path.normpath(args.input)
    output_path = os.path.normpath(args.output)

    if not os.path.exists(input_path):
        print(f'ERROR: input not found: {input_path}', file=sys.stderr)
        sys.exit(1)

    probes = load_probes(input_path)
    print(f'{len(probes)} probes loaded:')
    for p in probes:
        print(f'  {p.get("label","?")} | {p.get("timestamp","")[:19]}')

    shorts = [short_label(p.get('label', '?')) for p in probes]
    colors = COLORS[:len(probes)]

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    fig.suptitle(args.title, fontsize=13, fontweight='bold', y=1.01)

    for ax, (key, title, unit) in zip(axes.flat, METRICS):
        vals = [p.get(key, 0) or 0 for p in probes]
        x = np.arange(len(probes))
        bars = ax.bar(x, vals, color=colors, width=0.6, edgecolor='white', linewidth=0.8)
        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.set_ylabel(unit, fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels(shorts, fontsize=7)
        ax.tick_params(axis='y', labelsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        max_val = max(vals) if vals else 1
        for bar, val in zip(bars, vals):
            if val and val > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max_val * 0.01,
                    f'{val:.1f}',
                    ha='center', va='bottom', fontsize=7.5, fontweight='bold'
                )

    patches = [mpatches.Patch(color=colors[i], label=probes[i].get('label', str(i)))
               for i in range(len(probes))]
    fig.legend(handles=patches, loc='lower center', ncol=2, fontsize=8,
               bbox_to_anchor=(0.5, -0.06), frameon=True, framealpha=0.9)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f'Saved: {output_path}')


if __name__ == '__main__':
    main()
