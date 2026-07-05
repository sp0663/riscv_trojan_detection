#!/usr/bin/env python3
"""
method1_stage_aggregation.py — Per-stage / per-region toggle aggregation
════════════════════════════════════════════════════════════════════════════
Detection method 1 of 8.

What it does:
    Groups toggle counts by pipeline stage (IF/ID/EX/MEM/WB) and structural
    region (ALU, Forwarding, Hazard, RegFile, ...) for all 4 designs, then
    plots comparison bar charts.

    Aggregating by stage rather than individual wires gives a much more robust
    signal — small per-wire differences add up into clearly visible stage-level
    deviations, while per-wire noise averages out.

Why it catches Trojans:
    - Combinational Trojan (ALU): EX stage toggle count increases because
      the Trojan fires and ripples through ALU output -> EX_MEM register.
    - Sequential Trojan (counter): EX stage count increases significantly
      because the counter toggles on every ADD — continuous activity.
    - Control-path Trojan (forwarding): EX stage forwarding region has FEWER
      toggles (forwarding suppressed -> fewer mux switches downstream).

Outputs:
    plots/method1_stage_totals.png     — total toggles per stage per design
    plots/method1_region_breakdown.png — per-region breakdown within each stage
    plots/method1_deviation.png        — % deviation from clean per stage
    results/method1_summary.txt        — text summary with flagged regions
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict

# Local imports
sys.path.insert(0, os.path.dirname(__file__))
from vcd_parser import parse_vcd
from signal_stage_map import (STAGE_MAP, STAGE_ORDER, DESIGN_ORDER,
                               DESIGN_COLORS, get_stage_region)

# ── Config ────────────────────────────────────────────────────────────────
VCD_FILE        = "all_designs.vcd"
PLOTS_DIR       = "plots"
RESULTS_DIR     = "results"
DEVIATION_FLAG  = 10.0   # flag regions with >10% deviation from clean (%)

# ── Helpers ───────────────────────────────────────────────────────────────
def aggregate_by_stage(data: dict) -> dict:
    """
    Returns:
        stage_totals[design][stage]         = total toggle count
        region_totals[design][stage][region] = total toggle count
    """
    stage_totals  = {d: defaultdict(int) for d in DESIGN_ORDER}
    region_totals = {d: defaultdict(lambda: defaultdict(int)) for d in DESIGN_ORDER}

    for design in DESIGN_ORDER:
        if design not in data:
            continue
        for sig_name, info in data[design].items():
            stage, region = get_stage_region(sig_name)
            toggles = info['toggles']
            stage_totals[design][stage]          += toggles
            region_totals[design][stage][region] += toggles

    return stage_totals, region_totals


def pct_deviation(trojan_val, clean_val):
    if clean_val == 0:
        return 0.0
    return ((trojan_val - clean_val) / clean_val) * 100.0


# ── Plot 1: Stage totals bar chart ────────────────────────────────────────
def plot_stage_totals(stage_totals: dict, out_path: str):
    stages  = STAGE_ORDER
    designs = DESIGN_ORDER
    n_stages  = len(stages)
    n_designs = len(designs)

    x      = np.arange(n_stages)
    width  = 0.18
    offset = np.linspace(-(n_designs-1)/2, (n_designs-1)/2, n_designs) * width

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#1e1e2e')
    ax.set_facecolor('#1e1e2e')

    for i, design in enumerate(designs):
        vals = [stage_totals[design].get(s, 0) for s in stages]
        bars = ax.bar(x + offset[i], vals, width,
                      label=design,
                      color=DESIGN_COLORS[design],
                      alpha=0.85,
                      edgecolor='white',
                      linewidth=0.5)
        # Value labels on bars
        for bar, val in zip(bars, vals):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2,
                        bar.get_height() + 20,
                        str(val),
                        ha='center', va='bottom',
                        fontsize=7, color='white', rotation=45)

    ax.set_xticks(x)
    ax.set_xticklabels(stages, color='white', fontsize=12, fontweight='bold')
    ax.set_ylabel('Total Toggle Count', color='white', fontsize=11)
    ax.set_title('Method 1 — Toggle Count by Pipeline Stage\n'
                 '(clean vs combinational / sequential / control-path Trojan)',
                 color='white', fontsize=13, fontweight='bold')
    ax.tick_params(colors='white')
    ax.spines[:].set_color('#444')
    ax.yaxis.grid(True, color='#333', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    legend = ax.legend(fontsize=10, facecolor='#2d2d3e', labelcolor='white',
                       edgecolor='#555')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Saved: {out_path}")


# ── Plot 2: Deviation from clean per stage ────────────────────────────────
def plot_deviation(stage_totals: dict, out_path: str):
    stages   = STAGE_ORDER
    trojan_designs = [d for d in DESIGN_ORDER if d != 'clean']

    x      = np.arange(len(stages))
    width  = 0.22
    n      = len(trojan_designs)
    offset = np.linspace(-(n-1)/2, (n-1)/2, n) * width

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#1e1e2e')
    ax.set_facecolor('#1e1e2e')

    for i, design in enumerate(trojan_designs):
        devs = [pct_deviation(stage_totals[design].get(s, 0),
                              stage_totals['clean'].get(s, 0))
                for s in stages]
        bars = ax.bar(x + offset[i], devs, width,
                      label=design,
                      color=DESIGN_COLORS[design],
                      alpha=0.85,
                      edgecolor='white',
                      linewidth=0.5)
        for bar, dev in zip(bars, devs):
            if abs(dev) > 0.1:
                ax.text(bar.get_x() + bar.get_width()/2,
                        bar.get_height() + (0.3 if dev >= 0 else -1.2),
                        f'{dev:+.1f}%',
                        ha='center', va='bottom',
                        fontsize=8, color='white')

    # Flag threshold lines
    ax.axhline( DEVIATION_FLAG, color='yellow', linestyle='--',
                linewidth=1.2, alpha=0.8, label=f'+{DEVIATION_FLAG}% threshold')
    ax.axhline(-DEVIATION_FLAG, color='yellow', linestyle='--',
                linewidth=1.2, alpha=0.8)
    ax.axhline(0, color='white', linewidth=0.8, alpha=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(stages, color='white', fontsize=12, fontweight='bold')
    ax.set_ylabel('% Deviation from Clean', color='white', fontsize=11)
    ax.set_title('Method 1 — Stage-Level Toggle Deviation from Clean Design\n'
                 f'(yellow dashed = ±{DEVIATION_FLAG}% detection threshold)',
                 color='white', fontsize=13, fontweight='bold')
    ax.tick_params(colors='white')
    ax.spines[:].set_color('#444')
    ax.yaxis.grid(True, color='#333', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    legend = ax.legend(fontsize=10, facecolor='#2d2d3e',
                       labelcolor='white', edgecolor='#555')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Saved: {out_path}")


# ── Plot 3: Region breakdown heatmap ─────────────────────────────────────
def plot_region_heatmap(region_totals: dict, out_path: str):
    """
    Heatmap: rows = regions, cols = designs, values = % deviation from clean.
    Highlights exactly which structural block is anomalous.
    """
    # Collect all region names
    all_regions = set()
    for design in DESIGN_ORDER:
        for stage in STAGE_ORDER:
            all_regions.update(region_totals[design][stage].keys())
    all_regions = sorted(all_regions)

    trojan_designs = [d for d in DESIGN_ORDER if d != 'clean']
    matrix = np.zeros((len(all_regions), len(trojan_designs)))

    for j, design in enumerate(trojan_designs):
        for i, region in enumerate(all_regions):
            clean_val  = sum(region_totals['clean'][s].get(region, 0)
                             for s in STAGE_ORDER)
            trojan_val = sum(region_totals[design][s].get(region, 0)
                             for s in STAGE_ORDER)
            matrix[i, j] = pct_deviation(trojan_val, clean_val)

    fig, ax = plt.subplots(figsize=(8, max(6, len(all_regions) * 0.45)))
    fig.patch.set_facecolor('#1e1e2e')
    ax.set_facecolor('#1e1e2e')

    im = ax.imshow(matrix, cmap='RdYlGn_r', aspect='auto',
                   vmin=-30, vmax=30)

    ax.set_xticks(range(len(trojan_designs)))
    ax.set_xticklabels(trojan_designs, color='white', fontsize=11,
                       fontweight='bold')
    ax.set_yticks(range(len(all_regions)))
    ax.set_yticklabels(all_regions, color='white', fontsize=9)
    ax.tick_params(colors='white')

    # Annotate cells
    for i in range(len(all_regions)):
        for j in range(len(trojan_designs)):
            val = matrix[i, j]
            color = 'white' if abs(val) > 10 else '#aaa'
            ax.text(j, i, f'{val:+.1f}%', ha='center', va='center',
                    fontsize=8, color=color, fontweight='bold')

    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label('% deviation from clean', color='white', fontsize=9)
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color='white')

    ax.set_title('Method 1 — Region-Level Toggle Deviation Heatmap\n'
                 '(red = more toggles than clean, green = fewer)',
                 color='white', fontsize=12, fontweight='bold')
    ax.spines[:].set_color('#444')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Saved: {out_path}")


# ── Text summary ──────────────────────────────────────────────────────────
def write_summary(stage_totals, region_totals, out_path):
    lines = []
    lines.append("=" * 62)
    lines.append("METHOD 1 — Per-Stage Toggle Aggregation Summary")
    lines.append("=" * 62)
    lines.append("")

    # Stage totals
    header = f"{'Stage':<8}" + "".join(f"{d:>10}" for d in DESIGN_ORDER)
    lines.append(header)
    lines.append("-" * len(header))
    for stage in STAGE_ORDER:
        row = f"{stage:<8}"
        clean_val = stage_totals['clean'].get(stage, 0)
        for design in DESIGN_ORDER:
            val = stage_totals[design].get(stage, 0)
            if design == 'clean':
                row += f"{val:>10}"
            else:
                dev = pct_deviation(val, clean_val)
                row += f"{val:>6}({dev:+.1f}%)"
        lines.append(row)

    lines.append("")
    lines.append(f"FLAGGED REGIONS (deviation > ±{DEVIATION_FLAG}%):")
    lines.append("-" * 50)

    flagged = []
    for design in [d for d in DESIGN_ORDER if d != 'clean']:
        for stage in STAGE_ORDER:
            for region in region_totals[design][stage]:
                clean_val  = region_totals['clean'][stage].get(region, 0)
                trojan_val = region_totals[design][stage].get(region, 0)
                dev = pct_deviation(trojan_val, clean_val)
                if abs(dev) > DEVIATION_FLAG:
                    flagged.append((abs(dev), design, stage, region, dev,
                                    clean_val, trojan_val))

    flagged.sort(reverse=True)
    if flagged:
        for _, design, stage, region, dev, c_val, t_val in flagged:
            lines.append(f"  [{design}] {stage}/{region:<20} "
                         f"clean={c_val:>5}  trojan={t_val:>5}  "
                         f"dev={dev:+.1f}%")
    else:
        lines.append("  None found at current threshold.")

    lines.append("")
    lines.append("VERDICT:")
    for design in [d for d in DESIGN_ORDER if d != 'clean']:
        flags = [x for x in flagged if x[1] == design]
        if flags:
            lines.append(f"  {design:<6} -> SUSPICIOUS  "
                         f"({len(flags)} region(s) above threshold)")
        else:
            lines.append(f"  {design:<6} -> clean (no regions above threshold)")

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f"  Saved: {out_path}")
    # Also print to console
    print()
    for line in lines:
        print(line)


# ── Entry point ───────────────────────────────────────────────────────────
def run(vcd_path=VCD_FILE):
    os.makedirs(PLOTS_DIR,   exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print(f"\nMethod 1 — Per-Stage Toggle Aggregation")
    print(f"  Parsing {vcd_path} ...")
    data = parse_vcd(vcd_path)

    print("  Aggregating by stage and region ...")
    stage_totals, region_totals = aggregate_by_stage(data)

    print("  Generating plots ...")
    plot_stage_totals(stage_totals,
                      f"{PLOTS_DIR}/method1_stage_totals.png")
    plot_deviation(stage_totals,
                   f"{PLOTS_DIR}/method1_deviation.png")
    plot_region_heatmap(region_totals,
                        f"{PLOTS_DIR}/method1_region_heatmap.png")
    write_summary(stage_totals, region_totals,
                  f"{RESULTS_DIR}/method1_summary.txt")

    return data, stage_totals, region_totals


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--vcd', default=VCD_FILE)
    ap.add_argument('--threshold', type=float, default=DEVIATION_FLAG)
    args = ap.parse_args()
    DEVIATION_FLAG = args.threshold
    run(args.vcd)
