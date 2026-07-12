import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict
from vcd_parser import parse_vcd
from signal_stage_map import STAGE_ORDER, DESIGN_ORDER, DESIGN_COLORS, get_stage_region
from parse_netlist import process_netlist

spw = process_netlist('clean_netlist.json', 'PipelineCPU')
vcd_data  = parse_vcd("all_designs.vcd")

power_by_stage = {d: defaultdict(float) for d in DESIGN_ORDER}
for design in DESIGN_ORDER:
    for signal, info in vcd_data[design].items():
        stage, _ = get_stage_region(signal)
        power_by_stage[design][stage] += info['hamming_weight'] * spw.get(signal, 1)

def deviation(val, clean):
    return 0.0 if clean == 0 else ((val - clean) / clean) * 100.0

trojan_designs = [d for d in DESIGN_ORDER if d != 'clean']
x       = np.arange(len(STAGE_ORDER))
width   = 0.22
offsets = np.linspace(-(len(trojan_designs)-1)/2, (len(trojan_designs)-1)/2, len(trojan_designs)) * width

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('#F5F7FA')
ax.set_facecolor('#FFFFFF')

for i, design in enumerate(trojan_designs):
    devs = [deviation(power_by_stage[design].get(s, 0), power_by_stage['clean'].get(s, 0)) for s in STAGE_ORDER]
    ax.bar(x + offsets[i], devs, width, label=design, color=DESIGN_COLORS[design], alpha=0.85, edgecolor='white', linewidth=0.6)

ax.axhline(0,    color='#333333', linewidth=0.8, alpha=0.6)
ax.axhline( 10,  color='#B8860B', linewidth=1.4, linestyle='--', alpha=0.9, label='+/- 10% threshold')
ax.axhline(-10,  color='#B8860B', linewidth=1.4, linestyle='--', alpha=0.9)
ax.set_xticks(x)
ax.set_xticklabels(STAGE_ORDER, color='#1A1A2E', fontsize=12, fontweight='bold')
ax.set_ylabel('% Deviation from Clean', color='#1A1A2E', fontsize=11)
ax.set_title('Power Proxy Deviation from Clean per Stage', color='#1A1A2E', fontsize=13, fontweight='bold')
ax.tick_params(colors='#333333')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#CCCCCC')
ax.spines['bottom'].set_color('#CCCCCC')
ax.yaxis.grid(True, color='#DDDDDD', linestyle='--', alpha=0.8)
ax.set_axisbelow(True)
ax.legend(fontsize=10, facecolor='#F5F7FA', labelcolor='#1A1A2E', edgecolor='#CCCCCC', framealpha=1)
plt.tight_layout()
plt.savefig('deviation.png', dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()

lines = ["=" * 62, "Power Proxy Weighted Analysis Summary", "=" * 62, ""]
header = f"{'Stage':<8}" + "".join(f"{d:>14}" for d in DESIGN_ORDER)
lines += [header, "-" * len(header)]
for stage in STAGE_ORDER:
    row = f"{stage:<8}"
    clean_val = power_by_stage['clean'].get(stage, 0)
    for design in DESIGN_ORDER:
        val = power_by_stage[design].get(stage, 0)
        row += f"{val:>8.1f}" if design == 'clean' else f"  {val:.1f}({deviation(val, clean_val):+.1f}%)"
    lines.append(row)

lines += ["", "TOTAL:"]
clean_total = sum(power_by_stage['clean'].values())
for design in DESIGN_ORDER:
    total = sum(power_by_stage[design].values())
    lines.append(f"  {design:<6}: {total:.1f}" + (f"  ({deviation(total, clean_total):+.1f}% vs clean)" if design != 'clean' else ""))

with open('summary.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
