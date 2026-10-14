"""Supplementary Fig. 6a: Figure 1a colour bands with integrated terminal stage groups.

Run without arguments from any directory. The script uses only the CSV files
copied into this output package and preserves all 753 selected path rows.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
FIG_DIR = ROOT / 'figures'
QA_DIR = ROOT / "QA"
ORIGINAL_HELPERS = Path(__file__).with_name('original_plot_functions.py')
spec = importlib.util.spec_from_file_location("figure5b_original_helpers", ORIGINAL_HELPERS)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot load the archived original drawing functions")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

CLASS_ORDER = base.CLASS_ORDER
A_ORDER = base.A_ORDER
K_ORDER = base.K_ORDER
GROUPS = {
    "A01": "A01–02", "A02": "A01–02",
    "A03": "A03–04", "A04": "A03–04",
    "A05": "A05–07", "A06": "A05–07", "A07": "A05–07",
}
GROUP_ORDER = ("A01–02", "A03–04", "A05–07")

# Match Figure 1a's two three-stop colour bands and its clipped 0–70 linear
# normalization. Here the encoded measure is fractional project support.
PALETTE = {
    "NSF": {"light": "#E4EDF5", "mid": "#7F99B2", "dark": "#003366"},
    "NSFC": {"light": "#F6E4E4", "mid": "#C57F7F", "dark": "#8B0000"},
}
CMAPS = {
    "NSF": LinearSegmentedColormap.from_list(
        "nsf_target", [PALETTE["NSF"]["light"], PALETTE["NSF"]["mid"], PALETTE["NSF"]["dark"]]
    ),
    "NSFC": LinearSegmentedColormap.from_list(
        "nsfc_target", [PALETTE["NSFC"]["light"], PALETTE["NSFC"]["mid"], PALETTE["NSFC"]["dark"]]
    ),
}
SUPPORT_NORM = Normalize(vmin=0.0, vmax=70.0, clip=True)
TEXT = "#1F2933"
MUTED = "#657680"
RULE = "#C8D0D6"
ZERO = "#ECEFF1"

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "font.size": 7.2,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})


def stage_group_summary(paths: pd.DataFrame) -> pd.DataFrame:
    work = paths.copy()
    work["stage_group"] = work["action_stage"].map(GROUPS)
    if work["stage_group"].isna().any():
        raise ValueError("Unknown action-stage code")
    grouped = work.groupby(
        ["agency", "mismatch_class", "stage_group"], observed=True,
        as_index=False,
    )["fractional_project_support"].sum()
    panels = work[["agency", "mismatch_class"]].drop_duplicates()
    full = panels.merge(pd.DataFrame({"stage_group": GROUP_ORDER}), how="cross")
    full = full.merge(grouped, on=["agency", "mismatch_class", "stage_group"], how="left")
    full["fractional_project_support"] = full["fractional_project_support"].fillna(0.0)
    denominator = full.groupby(["agency", "mismatch_class"])["fractional_project_support"].transform("sum")
    full["share_within_panel_pct"] = 100 * full["fractional_project_support"] / denominator
    full["stage_group"] = pd.Categorical(full["stage_group"], GROUP_ORDER, ordered=True)
    return full.sort_values(["mismatch_class", "agency", "stage_group"]).reset_index(drop=True)


def _group_bounds(
    part: pd.DataFrame,
    scale: float,
    lower: float = 0.12,
    upper: float = 0.88,
    gap: float = 0.010,
) -> dict[str, tuple[float, float]]:
    totals = part.assign(stage_group=part.action_stage.map(GROUPS)).groupby(
        "stage_group", observed=True
    )["fractional_project_support"].sum()
    occupied = float(totals.sum()) * scale + gap * (len(GROUP_ORDER) - 1)
    cursor = lower + (upper - lower - occupied) / 2
    bounds = {}
    for group in GROUP_ORDER:
        height = float(totals.get(group, 0.0)) * scale
        bounds[group] = (cursor, cursor + height)
        cursor += height + gap
    return bounds


def _draw_terminal_groups(
    ax: plt.Axes,
    part: pd.DataFrame,
    stage_bounds: dict[tuple[int, str], tuple[float, float]],
    scale: float,
    group_bounds: dict[str, tuple[float, float]],
    agency: str,
    summary: pd.DataFrame,
    stage_x: float,
    group_x: float,
    node_width: float,
) -> None:
    stage_totals = part.groupby("action_stage", observed=True)["fractional_project_support"].sum()
    group_cursors = {group: group_bounds[group][0] for group in GROUP_ORDER}
    for stage in A_ORDER:
        if (3, stage) not in stage_bounds:
            continue
        group = GROUPS[stage]
        mass = float(stage_totals.get(stage, 0.0)) * scale
        dest = (group_cursors[group], group_cursors[group] + mass)
        group_cursors[group] += mass
        source = stage_bounds[(3, stage)]
        base._ribbon(
            ax,
            stage_x + node_width / 2 + 0.002,
            group_x - node_width / 2 - 0.002,
            source[0], source[1], dest[0], dest[1],
            PALETTE[agency]["light"], 1.0,
        )
    for group in GROUP_ORDER:
        if not np.isclose(group_cursors[group], group_bounds[group][1], atol=1e-9):
            raise ValueError(f"Stage-to-group flow does not conserve support: {agency} {group}")

    centers = [(group_bounds[group][0] + group_bounds[group][1]) / 2 for group in GROUP_ORDER]
    label_positions = base.spread_positions(centers, 0.22, 0.83, minimum_gap=0.122)
    share_lookup = dict(zip(summary.stage_group.astype(str), summary.share_within_panel_pct))
    for group, center, text_y in zip(GROUP_ORDER, centers, label_positions):
        y0, y1 = group_bounds[group]
        ax.add_patch(Rectangle(
            (group_x - node_width / 2, y0), node_width, max(y1 - y0, 0.0013),
            facecolor=PALETTE[agency]["light"], edgecolor=PALETTE[agency]["mid"],
            linewidth=0.48, zorder=3,
        ))
        if abs(text_y - center) > 0.005:
            ax.plot([group_x + node_width / 2, group_x + 0.012], [center, text_y],
                    color=RULE, linewidth=0.4, zorder=4)
        ax.text(
            group_x + 0.016, text_y,
            f"{group}  {share_lookup[group]:.1f}%",
            ha="left", va="center", fontsize=5.7, color=TEXT,
            fontweight="bold" if share_lookup[group] >= 10 else "normal",
            zorder=5,
        )


def draw_panel(
    ax: plt.Axes,
    paths: pd.DataFrame,
    agency: str,
    class_name: str,
    summary: pd.DataFrame,
    show_headers: bool,
) -> None:
    part = paths.loc[paths.agency.eq(agency) & paths.mismatch_class.eq(class_name)].copy()
    if part.empty:
        raise ValueError(f"No selected paths for {agency} / {class_name}")
    ax.set_facecolor("white")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(-0.10, 1.43)
    ax.set_ylim(0, 1)

    xs = [0.020, 0.280, 0.600, 0.840, 1.080]
    node_width = 0.011
    orders = base._node_orders(part)
    bounds, scale = base._node_bounds(part, orders, lower=0.12, upper=0.88)
    work = part.sort_values(["sdg", "target", "knowledge_task", "action_stage"]).reset_index(drop=True)
    intervals = base._path_intervals(work, orders, bounds, scale)
    group_bounds = _group_bounds(part, scale)
    panel_summary = summary.loc[summary.agency.eq(agency) & summary.mismatch_class.eq(class_name)]
    if len(panel_summary) != 3:
        raise ValueError("Each panel requires three stage-group values")

    # Colour all 753 individual paths with Figure 1a's continuous bands.
    # We draw stronger paths last so crossings do not hide their intensity.
    for index, row in work.sort_values("fractional_project_support").iterrows():
        color = CMAPS[agency](SUPPORT_NORM(float(row.fractional_project_support)))
        for layer in range(3):
            y0 = intervals[(layer, index)]
            y1 = intervals[(layer + 1, index)]
            base._ribbon(
                ax,
                xs[layer] + node_width / 2 + 0.002,
                xs[layer + 1] - node_width / 2 - 0.002,
                y0[0], y0[1], y1[0], y1[1], color, 1.0,
            )

    _draw_terminal_groups(
        ax, part, bounds, scale, group_bounds, agency, panel_summary,
        xs[3], xs[4], node_width,
    )

    columns = ["sdg", "target", "knowledge_task", "action_stage"]
    headers = ["SDG", "Formal Target", "Knowledge task", "A stage", "A-group share"]
    if show_headers:
        for x, label in zip(xs, headers):
            ax.text(x, 0.982, label, ha="center", va="top", fontsize=5.65,
                    color=TEXT, fontweight="bold", zorder=7)
    for layer, (column, order) in enumerate(zip(columns, orders)):
        x = xs[layer]
        centers = [(bounds[(layer, item)][0] + bounds[(layer, item)][1]) / 2 for item in order]
        if layer == 0:
            label_positions = centers
        else:
            gaps = {1: 0.054, 2: 0.070, 3: 0.060}
            label_positions = base.spread_positions(centers, 0.18, 0.88, gaps[layer])
        for item, center, text_y in zip(order, centers, label_positions):
            y0, y1 = bounds[(layer, item)]
            fill = ZERO
            if layer == 0:
                fill = PALETTE[agency]["light"]
            elif layer == 1 and item.endswith(":Other"):
                fill = "#DDE3E7"
            elif layer == 3:
                fill = PALETTE[agency]["light"]
            ax.add_patch(Rectangle(
                (x - node_width / 2, y0), node_width, max(y1 - y0, 0.0013),
                facecolor=fill, edgecolor=MUTED, linewidth=0.43, zorder=3,
            ))
            if layer == 0:
                text, tx, ha = item.replace("S", "SDG"), x - 0.011, "right"
            elif layer == 1:
                text, tx, ha = base._target_display_label(part, item), x + 0.010, "left"
            elif layer == 2:
                text, tx, ha = item, x + 0.010, "left"
            else:
                text, tx, ha = item, x + 0.010, "left"
            if layer > 0 and abs(text_y - center) > 0.005:
                ax.plot([x + node_width / 2, tx - 0.002], [center, text_y],
                        color=RULE, linewidth=0.35, zorder=4)
            ax.text(tx, text_y, text, ha=ha, va="center",
                    fontsize=5.25 if layer == 1 else 5.65,
                    color=TEXT, zorder=5,
                    path_effects=[pe.withStroke(linewidth=1.65, foreground="white")])


def render(paths: pd.DataFrame, summary: pd.DataFrame) -> plt.Figure:
    fig = plt.figure(figsize=(9.0, 6.5), facecolor="white")
    grid = fig.add_gridspec(
        3, 2, left=0.055, right=0.982, bottom=0.125, top=0.865,
        hspace=0.20, wspace=0.11,
    )
    axes = {}
    for row, class_name in enumerate(CLASS_ORDER):
        for column, agency in enumerate(("NSF", "NSFC")):
            ax = fig.add_subplot(grid[row, column])
            draw_panel(ax, paths, agency, class_name, summary, show_headers=row == 0)
            axes[row, agency] = ax
        axes[row, "NSF"].text(
            -0.065, 1.025, class_name.replace(" research supply", ""),
            transform=axes[row, "NSF"].transAxes, ha="left", va="bottom",
            fontsize=6.9, fontweight="bold", color=TEXT,
        )

    fig.text(0.016, 0.982, "a", va="top", fontsize=12.0,
             fontweight="bold", color=TEXT)
    fig.text(
        0.057, 0.979, "Internal organization of stable supply–challenge positions",
        va="top", fontsize=10.3, fontweight="bold", color=TEXT,
    )
    fig.text(
        0.057, 0.948,
        "Stable SDGs → formal Targets → K01–K06 → A01–A07 → grouped highest stated action stage",
        va="top", fontsize=6.65, color=MUTED,
    )
    fig.text(0.985, 0.980, "Project-count stability gate", ha="right", va="top",
             fontsize=6.0, color=MUTED, fontstyle="italic")
    fig.text(0.283, 0.906, "NSF", ha="center", va="bottom", fontsize=9.5,
             fontweight="bold", color=PALETTE["NSF"]["dark"])
    fig.text(0.755, 0.906, "NSFC", ha="center", va="bottom", fontsize=9.5,
             fontweight="bold", color=PALETTE["NSFC"]["dark"])
    for agency, left in (("NSF", 0.165), ("NSFC", 0.585)):
        cax = fig.add_axes([left, 0.049, 0.250, 0.009])
        cbar = fig.colorbar(
            mpl.cm.ScalarMappable(norm=SUPPORT_NORM, cmap=CMAPS[agency]),
            cax=cax, orientation="horizontal",
        )
        cbar.set_ticks([0, 10, 30, 50, 70])
        cbar.set_ticklabels(["0", "10", "30", "50", "≥70"])
        cbar.ax.tick_params(length=0, labelsize=5.7, pad=1.0)
        cbar.outline.set_visible(False)
        cbar.ax.set_title(f"{agency} path support", fontsize=6.2, pad=2.2, color=TEXT)
    fig.text(
        0.5, 0.014,
        "Ribbon width and colour = fractional project support; terminal percentages = within-panel shares. Shared linear colour scale; values ≥70 saturate.",
        ha="center", va="center", fontsize=5.85, color=MUTED,
    )
    return fig


def verify(paths: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    if len(paths) != 753:
        raise ValueError(f"Expected the 753 selected original paths, got {len(paths)}")
    if paths.duplicated(["agency", "mismatch_class", "sdg", "target", "knowledge_task", "action_stage"]).any():
        raise ValueError("Duplicate four-layer paths")
    if (paths.fractional_project_support <= 0).any():
        raise ValueError("Nonpositive selected path support")
    source = paths.groupby(["agency", "mismatch_class"])["fractional_project_support"].sum()
    grouped = summary.groupby(["agency", "mismatch_class"])["fractional_project_support"].sum()
    delta = (source - grouped).abs()
    if float(delta.max()) > 1e-9:
        raise ValueError("Stage-group totals do not conserve selected path support")
    closure = summary.groupby(["agency", "mismatch_class"])["share_within_panel_pct"].sum()
    if not np.allclose(closure, 100, atol=1e-9):
        raise ValueError("Panel shares do not close at 100%")
    return pd.DataFrame({"path_support": source, "group_support": grouped,
                         "absolute_error": delta, "share_sum_pct": closure}).reset_index()


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)
    path_file = DATA_DIR / 'Supplementary_Fig_6a_stable_entry_full_paths.csv'
    paths = pd.read_csv(path_file, encoding="utf-8-sig")
    summary = stage_group_summary(paths)
    closure = verify(paths, summary)
    summary.to_csv(DATA_DIR / 'Supplementary_Fig_6a_terminal_three_group_action_stage_shares.csv', index=False, encoding="utf-8-sig")
    closure.to_csv(QA_DIR / 'Supplementary_Fig_6a_terminal_flow_conservation.csv', index=False, encoding="utf-8-sig")
    fig = render(paths, summary)
    stem = FIG_DIR / 'Supplementary_Fig_6a_light_palette_sankey_and_terminal_stage_groups'
    for suffix in (".svg", ".pdf", ".png", ".tiff"):
        output = stem.with_suffix(suffix)
        if suffix == ".png":
            fig.savefig(output, dpi=330, facecolor="white")
        elif suffix == ".tiff":
            fig.savefig(output, dpi=600, facecolor="white",
                        pil_kwargs={"compression": "tiff_lzw"})
        else:
            fig.savefig(output, facecolor="white")
    plt.close(fig)
    report = {
        "source_sha256": hashlib.sha256(path_file.read_bytes()).hexdigest(),
        "path_rows": len(paths),
        "panel_count": len(closure),
        "largest_mass_error": float(closure.absolute_error.max()),
        "largest_share_error_pp": float((closure.share_sum_pct - 100).abs().max()),
        "palette": PALETTE,
        "colour_scale": {"measure": "fractional_project_support", "vmin": 0.0,
                         "vmax": 70.0, "clip": True, "alpha": 1.0},
        "figure_files": [str(stem.with_suffix(ext)) for ext in (".svg", ".pdf", ".png", ".tiff")],
    }
    (QA_DIR / 'Supplementary_Fig_6a_reconstructed_checks.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
