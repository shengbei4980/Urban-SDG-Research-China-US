"""Recompute and plot Supplementary Fig. 8b from administrative-location allocations.

Uses the corrected Supplementary Fig. 8b administrative-location definition.
Run from any working directory: python code/plot_supplementary_fig_8b.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
INPUT = DATA / 'input_snapshots'
OUT = ROOT / 'outputs'
OUT.mkdir(exist_ok=True)

def jsd(p, q):
    midpoint = (p + q) / 2
    contributions = []
    for x in (p, q):
        z = np.zeros_like(x)
        positive = x > 0
        z[positive] = x[positive] * np.log2(x[positive] / midpoint[positive])
        contributions.append(z.sum(axis=1))
    return (contributions[0] + contributions[1]) / 2

def calculate():
    allocations = pd.read_csv(INPUT / 'project_level_target_task_allocations.csv')
    keys = ['agency', 'unit_id']
    tasks = allocations.groupby(keys + ['sdg', 'task']).supply.sum().unstack('task', fill_value=0)
    national = tasks.groupby(level=['agency', 'sdg']).sum()
    values = tasks.to_numpy()
    total = np.stack([national.loc[(a, s)].to_numpy() for a, u, s in tasks.index])
    rest = total - values
    assert rest.min() > -1e-8
    rest = np.maximum(rest, 0)
    assert (values.sum(axis=1) > 0).all() and (rest.sum(axis=1) > 0).all()
    p = values / values.sum(axis=1, keepdims=True)
    q = rest / rest.sum(axis=1, keepdims=True)
    goals = tasks.reset_index()[keys + ['sdg']].copy()
    goals['supply'] = values.sum(axis=1)
    goals['jsd_rest_bits'] = jsd(p, q)
    goals['weighted'] = goals.supply * goals.jsd_rest_bits
    locations = goals.groupby(keys).agg(supply=('supply', 'sum'), weighted=('weighted', 'sum'))
    locations['jsd_rest_bits'] = locations.weighted / locations.supply
    locations['family_n'] = allocations.groupby(keys).project_family_id.nunique()
    locations['F'] = locations.supply / locations.groupby(level='agency').supply.transform('sum')
    locations = locations.reset_index()
    assert locations.groupby('agency').size().to_dict() == {'NSF': 352, 'NSFC': 126}
    assert np.allclose(locations.groupby('agency').supply.sum(), [5000, 5546])
    existing = pd.read_csv(INPUT / 'Figure3b_full_478_locations.csv')
    comparison = locations.merge(existing, on=keys, suffixes=('', '_original'), validate='one_to_one')
    error = float((comparison.jsd_rest_bits - comparison.jsd_rest_bits_original).abs().max())
    assert error < 1e-12
    assert np.array_equal(comparison.family_n, comparison.family_n_original)
    rows = []
    for agency, group in locations.groupby('agency'):
        for threshold in [0, 10, 20, 30]:
            retained = group[group.family_n >= threshold]
            rows.append(dict(agency=agency, minimum_families=threshold, retained_locations=len(retained),
                             median_jsd_rest_bits=float(retained.jsd_rest_bits.median()),
                             excluded_supply_pct=max(0., float(100 * (1 - retained.F.sum())))))
    summary = pd.DataFrame(rows)
    locations.to_csv(DATA / 'Supplementary_Fig_8b_location_metrics.csv', index=False, encoding='utf-8-sig')
    summary.to_csv(DATA / 'Supplementary_Fig_8b_source_data.csv', index=False, encoding='utf-8-sig')
    return summary, error

def plot(summary):
    # Style inheritance only. Recompute the statistic from administrative locations.
    plt.rcParams.update({'font.family': 'Arial', 'font.size': 8,
                         'svg.fonttype': 'none', 'pdf.fonttype': 42,
                         'axes.linewidth': 0.7, 'legend.frameon': False})
    width_mm = 183
    width, height = 2385, 2310
    split = 1280  # Blank boundary between the unchanged panel a and redrawn panel b.
    panel_height = height - split
    fig = plt.figure(figsize=(width_mm / 25.4, width_mm * panel_height / width / 25.4))
    ax = fig.add_axes([0.071, 0.195, 0.876, 0.665])
    bars = ax.twinx()
    ax.set_zorder(2)
    ax.patch.set_visible(False)
    colours = {'NSF': '#003366', 'NSFC': '#8B0000'}
    light = {'NSF': '#7F99B2', 'NSFC': '#C57F7F'}
    markers = {'NSF': 'o', 'NSFC': 's'}
    for i, agency in enumerate(['NSF', 'NSFC']):
        subset = summary[summary.agency == agency]
        x = subset.minimum_families.to_numpy()
        y = subset.median_jsd_rest_bits.to_numpy()
        bars.bar(x + (-1.15 if i == 0 else 1.15), subset.excluded_supply_pct, width=2.25,
                 color=light[agency], alpha=0.20, edgecolor=colours[agency], linewidth=0.7)
        ax.plot(x, y, color=colours[agency], marker=markers[agency], markersize=5,
                markeredgecolor='white', markeredgewidth=0.6, linewidth=1.65)
        guide = np.polyval(np.polyfit(x, y, 1), x)
        ax.plot(x, guide, color=light[agency], linestyle=(0, (5, 3)), linewidth=1.1)
        ax.annotate(f'{y[-1]:.3f}', (x[-1], y[-1]), xytext=(6, 5 if i == 0 else -10),
                    textcoords='offset points', fontsize=8, fontweight='bold', color=colours[agency])
    ax.set(xlim=(-3.4, 33.4), ylim=(0.04, 0.375), xticks=[0, 10, 20, 30],
           yticks=np.arange(0.05, 0.36, 0.05), xlabel='Minimum project families per administrative location',
           ylabel='Median within-goal task JSD (bits)')
    bars.set(ylim=(42, 0), yticks=[0, 10, 20, 30, 40], ylabel='Research supply excluded (%)')
    ax.grid(axis='y', color='#E1E5E9', linewidth=0.55)
    for axis in (ax, bars):
        axis.tick_params(labelsize=7.5, length=3, colors='#35414C')
        for spine in axis.spines.values():
            spine.set_color('#53606D')
    ax.set_title('Administrative-location task differences across support thresholds', fontsize=9.2, pad=8)
    fig.text(0.003, 0.92, 'b', fontweight='bold', fontsize=10.5)
    handles = [Line2D([], [], color=colours[a], marker=markers[a], linewidth=1.5, markersize=4.5, label=f'{a} JSD') for a in ['NSF', 'NSFC']]
    handles += [Patch(facecolor=light[a], edgecolor=colours[a], alpha=0.3, label=f'{a} supply excluded') for a in ['NSF', 'NSFC']]
    handles += [Line2D([], [], color='#8B99A5', linestyle='--', label='Linear guide')]
    fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, 0.005), ncol=5,
               fontsize=7.3, columnspacing=1.25, handlelength=2, handletextpad=0.5)
    fig.savefig(OUT / 'Supplementary_Fig_8b.svg', facecolor='white')
    fig.savefig(OUT / 'Supplementary_Fig_8b.pdf', facecolor='white')
    fig.savefig(OUT / 'Supplementary_Fig_8b.png', dpi=600, facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    summary, error = calculate()
    plot(summary)
    print(summary.to_string(index=False))
    print(f'Maximum JSD difference from the Fig. 3b reference: {error:.3g}')
