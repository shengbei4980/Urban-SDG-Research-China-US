from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
import numpy as np
import pandas as pd


FIGURE1_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FIGURE1_ROOT))



NSF_COLOR = "#003366"
NSFC_COLOR = "#8B0000"
GRID_COLOR = "#D9DEE3"
YEARS = list(range(2015,2026))
DEFAULT_REMAINDER = Path(__file__).resolve().parent / "figure1b剩余"
TOP_CODES_PER_DIMENSION = 5
SEMANTIC_DIMENSIONS = (
    ("Urban needs", "urban_need_topic_multi", tuple(f"N{i:02d}" for i in range(1, 20))),
    ("Problem pressures", "urban_pressure_type", tuple(f"P{i:02d}" for i in range(1, 9))),
    ("Urban systems", "urban_system_type", tuple(f"O{i:02d}" for i in range(1, 13))),
    ("Knowledge tasks", "knowledge_task_multi", tuple(f"K{i:02d}" for i in range(1, 7))),
    ("Intervention modes", "intervention_type_multi", tuple(f"L{i:02d}" for i in range(1, 10))),
    ("Action stages", "research_action_stage", tuple(f"A{i:02d}" for i in range(1, 8))),
)
FIGURE1A_PALETTES = {
    "NSF": ("#E4EDF5", "#7F99B2", NSF_COLOR),
    "NSFC": ("#F6E4E4", "#C57F7F", NSFC_COLOR),
}
OTHER_COLOR = "#ECEFF1"
COUNTRY_CMAPS = {
    agency: mpl.colors.LinearSegmentedColormap.from_list(f"figure1a_{agency.lower()}", stops)
    for agency, stops in FIGURE1A_PALETTES.items()
}


def country_rank_color(agency: str, rank: int, total_ranks: int = TOP_CODES_PER_DIMENSION) -> str:
    """Figure 1a country ramp, from darkest first rank to lightest last rank."""
    if total_ranks < 1 or not 1 <= rank <= total_ranks:
        raise ValueError((agency, rank, total_ranks))
    position = 1.0 if total_ranks == 1 else 1.0 - (rank - 1) / (total_ranks - 1)
    return mpl.colors.to_hex(COUNTRY_CMAPS[agency](position))


def configure_matplotlib() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": 7,
            "axes.unicode_minus": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.7,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def _agency_table(annual: pd.DataFrame, agency: str) -> pd.DataFrame:
    return annual.loc[annual["agency"].eq(agency)].sort_values("year").reset_index(drop=True)








def _dimension_groups(mapping: pd.DataFrame, dimension: str) -> list[str]:
    selected = (
        mapping.loc[mapping["dimension"].eq(dimension) & mapping["shown_individually_in_main"]]
        .sort_values("main_display_rank")["code"]
        .tolist()
    )
    return selected + ["Other"]


def _plot_supported_line(
    ax: plt.Axes,
    table: pd.DataFrame,
    value: str,
    ci_low: str,
    ci_high: str,
    color: str,
    marker: str,
    linestyle: str,
) -> None:
    supported = table["n_projects"].ge(30).to_numpy()
    x = table["year"].to_numpy(dtype=float)
    y = table[value].to_numpy(dtype=float)
    low = table[ci_low].to_numpy(dtype=float)
    high = table[ci_high].to_numpy(dtype=float)
    ax.plot(
        x,
        np.where(supported, y, np.nan),
        color=color,
        linewidth=1.4,
        linestyle=linestyle,
        marker=marker,
        markersize=3.4,
        zorder=4,
    )
    ax.fill_between(x, low, high, where=supported, color=color, alpha=0.085, linewidth=0, zorder=1)
    low_support = (~supported) & table["n_projects"].gt(0).to_numpy() & np.isfinite(y)
    supported_indices = np.flatnonzero(supported)
    low_indices = np.flatnonzero(low_support)
    if len(low_indices):
        tail = low_indices[low_indices > supported_indices.max()] if len(supported_indices) else low_indices
        if len(tail):
            join = np.r_[supported_indices.max(), tail] if len(supported_indices) else tail
            ax.plot(x[join], y[join], color=color, linewidth=0.9, linestyle=(0, (1.2, 2.0)), alpha=0.72)
        ax.scatter(
            x[low_support],
            y[low_support],
            marker=marker,
            s=21,
            facecolor="white",
            edgecolor=color,
            linewidth=0.9,
            zorder=5,
        )


def _draw_semantic_row(
    ax: plt.Axes,
    main: pd.DataFrame,
    mapping: pd.DataFrame,
    dimension: str,
    show_low_support_n: bool,
) -> None:
    groups = _dimension_groups(mapping, dimension)
    width = 0.34
    for agency, offset, edge_color in (("NSF", -0.19, NSF_COLOR), ("NSFC", 0.19, NSFC_COLOR)):
        color_by_group = {
            group: country_rank_color(agency, index + 1) if group != "Other" else OTHER_COLOR
            for index, group in enumerate(groups)
        }
        subset = main.loc[main["agency"].eq(agency) & main["dimension"].eq(dimension)]
        n_by_year = subset.groupby("year")["n_projects"].max().reindex(YEARS, fill_value=0)
        bottom = np.zeros(len(YEARS), dtype=float)
        for group in groups:
            values = (
                subset.loc[subset["main_display_group"].eq(group)]
                .set_index("year")["share_pct"]
                .reindex(YEARS)
                .to_numpy(dtype=float)
            )
            heights = np.nan_to_num(values, nan=0.0)
            ax.bar(
                np.asarray(YEARS, dtype=float) + offset,
                heights,
                width=width,
                bottom=bottom,
                color=color_by_group[group],
                edgecolor="white",
                linewidth=0.18,
                zorder=2,
            )
            bottom += heights
        for year, n_projects in n_by_year.items():
            center = year + offset
            if n_projects == 0:
                ax.plot(center, 50, marker="x", color=edge_color, markersize=3.2, markeredgewidth=0.8, zorder=5)
                continue
            linestyle = (0, (1.2, 1.2)) if n_projects < 30 else "-"
            ax.add_patch(
                Rectangle(
                    (center - width / 2, 0),
                    width,
                    100,
                    fill=False,
                    edgecolor=edge_color,
                    linewidth=0.55 if n_projects >= 30 else 0.85,
                    linestyle=linestyle,
                    zorder=4,
                )
            )
            if n_projects < 30 and show_low_support_n:
                ax.text(center, 102.5, f"{n_projects}", ha="center", va="bottom", fontsize=5.0, color=edge_color)

    top_codes = groups[:-1]
    ax.text(0.0, 1.025, dimension, transform=ax.transAxes, ha="left", va="bottom", fontweight="bold", fontsize=6.6)
    ax.text(
        1.0,
        1.025,
        "Top 5: " + " · ".join(top_codes),
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=5.0,
        color="#56616B",
    )
    ax.set_ylim(0, 108)
    ax.set_xlim(min(YEARS) - 0.62, max(YEARS) + 0.62)
    ax.set_yticks([0, 50, 100])
    ax.set_ylabel("Share (%)", labelpad=3)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.45, zorder=0)
    ax.set_xticks(YEARS)
    ax.tick_params(axis="x", labelbottom=False, length=0)
    ax.tick_params(axis="y", labelsize=5.6, length=2, pad=2)


def draw_main_figure(annual: pd.DataFrame, main: pd.DataFrame, mapping: pd.DataFrame) -> plt.Figure:
    configure_matplotlib()
    fig = plt.figure(figsize=(7.0866, 7.55))
    grid = fig.add_gridspec(
        7,
        1,
        height_ratios=[1, 1, 1, 1, 1, 1, 1.72],
        left=0.095,
        right=0.985,
        top=0.922,
        bottom=0.075,
        hspace=0.23,
    )
    for index, (dimension, _, _) in enumerate(SEMANTIC_DIMENSIONS):
        ax = fig.add_subplot(grid[index])
        _draw_semantic_row(ax, main, mapping, dimension, show_low_support_n=index == 0)

    trend_ax = fig.add_subplot(grid[6])
    annual_plot = annual.copy()
    annual_plot["target_coverage_pct"] = annual_plot["observed_target_breadth"] / 121.0 * 100.0
    annual_plot["target_coverage_ci_low_pct"] = annual_plot["breadth_bootstrap_ci_low"] / 121.0 * 100.0
    annual_plot["target_coverage_ci_high_pct"] = annual_plot["breadth_bootstrap_ci_high"] / 121.0 * 100.0
    annual_plot["target_evenness_pct"] = annual_plot["pielou_evenness"] * 100.0
    annual_plot["target_evenness_ci_low_pct"] = annual_plot["evenness_bootstrap_ci_low"] * 100.0
    annual_plot["target_evenness_ci_high_pct"] = annual_plot["evenness_bootstrap_ci_high"] * 100.0
    for agency, color in (("NSF", NSF_COLOR), ("NSFC", NSFC_COLOR)):
        table = _agency_table(annual_plot, agency)
        _plot_supported_line(
            trend_ax,
            table,
            "target_coverage_pct",
            "target_coverage_ci_low_pct",
            "target_coverage_ci_high_pct",
            color,
            marker="o",
            linestyle="-",
        )
        _plot_supported_line(
            trend_ax,
            table,
            "target_evenness_pct",
            "target_evenness_ci_low_pct",
            "target_evenness_ci_high_pct",
            color,
            marker="D",
            linestyle="--",
        )
    trend_ax.set_xlim(min(YEARS) - 0.5, max(YEARS) + 0.5)
    trend_ax.set_ylim(0, 100)
    trend_ax.set_xticks(YEARS)
    trend_ax.set_xticklabels([str(year) for year in YEARS], fontsize=6.3)
    trend_ax.set_yticks([0, 25, 50, 75, 100])
    trend_ax.set_ylabel("Target structure (%)")
    trend_ax.set_xlabel("Award / ratification year")
    trend_ax.grid(axis="y", color=GRID_COLOR, linewidth=0.5)
    trend_ax.text(
        0.0,
        1.025,
        "Formal Target coverage and target-composition evenness",
        transform=trend_ax.transAxes,
        ha="left",
        va="bottom",
        fontweight="bold",
        fontsize=6.7,
    )

    country_handles = [
        Patch(facecolor=NSF_COLOR, edgecolor="none", label="NSF · blue rank scale"),
        Patch(facecolor=NSFC_COLOR, edgecolor="none", label="NSFC · red rank scale"),
        Patch(facecolor=OTHER_COLOR, edgecolor="#B9C1C8", linewidth=0.4, label="Other"),
    ]
    fig.legend(
        handles=country_handles,
        loc="upper center",
        bbox_to_anchor=(0.54, 0.974),
        ncol=3,
        frameon=False,
        fontsize=5.5,
        handlelength=1.1,
        handleheight=0.8,
        columnspacing=0.8,
    )
    trend_handles = [
        Line2D([0], [0], color=NSF_COLOR, lw=1.4, label="NSF"),
        Line2D([0], [0], color=NSFC_COLOR, lw=1.4, label="NSFC"),
        Line2D([0], [0], color="#39434C", marker="o", lw=1.2, label="Target coverage"),
        Line2D([0], [0], color="#39434C", marker="D", lw=1.2, ls="--", label="Target evenness"),
        Patch(facecolor="#7C8791", alpha=0.16, edgecolor="none", label="Project bootstrap 95% CI"),
        Line2D(
            [0],
            [0],
            color="#4E5963",
            marker="o",
            markerfacecolor="white",
            linestyle=(0, (1.2, 2.0)),
            markersize=3.8,
            label="0<n<30; no CI",
        ),
    ]
    trend_ax.legend(
        handles=trend_handles,
        loc="center",
        bbox_to_anchor=(0.5, 0.61),
        ncol=3,
        frameon=False,
        fontsize=5.7,
        handlelength=1.6,
        columnspacing=0.9,
    )
    fig.text(
        0.095,
        0.946,
        "Annual within-dimension composition · darker colour = higher pooled rank · low-support n labelled above",
        ha="left",
        va="center",
        fontsize=5.8,
        color="#56616B",
    )
    fig.text(0.016, 0.98, "", fontsize=8, fontweight="bold", ha="left", va="top")
    return fig


def _dimension_slug(dimension: str) -> str:
    return dimension.lower().replace(" ", "_")


def _remaining_codes(mapping: pd.DataFrame, dimension: str) -> list[str]:
    remaining = (
        mapping.loc[mapping["dimension"].eq(dimension) & ~mapping["shown_individually_in_main"]]
        .sort_values("pooled_rank")["code"]
        .tolist()
    )
    if not remaining:
        raise ValueError(f"{dimension}: no categories remain after top-five selection")
    return remaining


def _remaining_colors(codes: list[str], agency: str) -> dict[str, str]:
    """Use the corresponding Figure 1a country ramp for all retained codes."""
    return {code: country_rank_color(agency, rank, len(codes))
            for rank, code in enumerate(codes, start=1)}


def _remaining_y_scale(full: pd.DataFrame, dimension: str, remaining: list[str]) -> tuple[float, float]:
    remaining_full = full.loc[full["dimension"].eq(dimension) & full["code"].isin(remaining)]
    annual_remaining_share = remaining_full.groupby(["agency", "year"])["share_pct"].sum(min_count=1)
    observed_max = float(annual_remaining_share.max(skipna=True)) if annual_remaining_share.notna().any() else 0.0
    y_max = max(5.0, float(np.ceil(observed_max * 1.08 / 5.0) * 5.0))
    y_step = 1.0 if y_max <= 5 else 5.0 if y_max <= 30 else 10.0
    return y_max, y_step


def _draw_remaining_row(
    ax: plt.Axes,
    full: pd.DataFrame,
    mapping: pd.DataFrame,
    dimension: str,
    *,
    show_low_support_n: bool,
    show_x_labels: bool,
) -> None:
    remaining = _remaining_codes(mapping, dimension)
    y_max, y_step = _remaining_y_scale(full, dimension, remaining)
    width = 0.34
    for agency, offset, edge_color in (("NSF", -0.19, NSF_COLOR), ("NSFC", 0.19, NSFC_COLOR)):
        colors = _remaining_colors(remaining, agency)
        subset = full.loc[
            full["agency"].eq(agency) & full["dimension"].eq(dimension) & full["code"].isin(remaining)
        ]
        bottom = np.zeros(len(YEARS), dtype=float)
        for code in remaining:
            values = (
                subset.loc[subset["code"].eq(code)]
                .set_index("year")["share_pct"]
                .reindex(YEARS)
                .to_numpy(dtype=float)
            )
            heights = np.nan_to_num(values, nan=0.0)
            ax.bar(
                np.asarray(YEARS, dtype=float) + offset,
                heights,
                width=width,
                bottom=bottom,
                color=colors[code],
                edgecolor="white",
                linewidth=0.18,
                zorder=2,
            )
            bottom += heights
        n_by_year = subset.groupby("year")["n_projects"].max().reindex(YEARS, fill_value=0)
        for index, (year, n_projects) in enumerate(n_by_year.items()):
            center = year + offset
            height = bottom[index]
            if n_projects == 0:
                ax.plot(center, y_max * 0.5, marker="x", color=edge_color, markersize=3.2, markeredgewidth=0.8, zorder=5)
                continue
            linestyle = (0, (1.2, 1.2)) if n_projects < 30 else "-"
            ax.add_patch(
                Rectangle(
                    (center - width / 2, 0),
                    width,
                    height,
                    fill=False,
                    edgecolor=edge_color,
                    linewidth=0.55 if n_projects >= 30 else 0.85,
                    linestyle=linestyle,
                    zorder=4,
                )
            )
            if n_projects < 30 and show_low_support_n:
                ax.text(
                    center,
                    min(y_max * 0.97, height + y_max * 0.025),
                    f"{n_projects}",
                    ha="center",
                    va="bottom",
                    fontsize=5.0,
                    color=edge_color,
                )

    ax.text(0.0, 1.025, dimension, transform=ax.transAxes, ha="left", va="bottom", fontweight="bold", fontsize=6.6)
    ax.text(1.0, 1.025, "Bottom → top: " + " · ".join(remaining),
            transform=ax.transAxes, ha="right", va="bottom", fontsize=5.0,
            color="#56616B")
    ax.set_xlim(min(YEARS) - 0.62, max(YEARS) + 0.62)
    ax.set_ylim(0, y_max)
    ax.set_yticks(np.arange(0, y_max + y_step * 0.5, y_step))
    ax.set_ylabel("Share (%)", labelpad=3)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.45, zorder=0)
    ax.set_xticks(YEARS)
    if show_x_labels:
        ax.set_xticklabels([str(year) for year in YEARS], fontsize=6.0)
        ax.set_xlabel("Award / ratification year")
    else:
        ax.tick_params(axis="x", labelbottom=False, length=0)
    ax.tick_params(axis="y", labelsize=5.6, length=2, pad=2)


def draw_remaining_dimension(full: pd.DataFrame, mapping: pd.DataFrame, dimension: str) -> plt.Figure:
    configure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.0866, 2.65))
    _draw_remaining_row(
        ax,
        full,
        mapping,
        dimension,
        show_low_support_n=True,
        show_x_labels=True,
    )
    country_handles = [
        Patch(facecolor=NSF_COLOR, edgecolor="none", label="NSF"),
        Patch(facecolor=NSFC_COLOR, edgecolor="none", label="NSFC"),
        Patch(facecolor="white", edgecolor="#4E5963", linewidth=0.8, linestyle=(0, (1.2, 1.2)), label="0<n<30"),
    ]
    fig.legend(
        handles=country_handles,
        loc="upper left",
        bbox_to_anchor=(0.088, 0.98),
        ncol=3,
        frameon=False,
        fontsize=5.5,
        handlelength=1.0,
        columnspacing=0.8,
    )
    fig.suptitle(
        "Categories represented by Other in the main Figure 1b",
        x=0.985,
        y=0.968,
        ha="right",
        fontsize=5.8,
        color="#56616B",
    )
    fig.subplots_adjust(left=0.09, right=0.985, top=0.77, bottom=0.19)
    return fig


def draw_remaining_combined(full: pd.DataFrame, mapping: pd.DataFrame) -> plt.Figure:
    configure_matplotlib()
    fig = plt.figure(figsize=(7.0866, 7.1))
    grid = fig.add_gridspec(
        len(SEMANTIC_DIMENSIONS),
        1,
        left=0.095,
        right=0.985,
        top=0.915,
        bottom=0.075,
        hspace=0.48,
    )
    for index, (dimension, _, _) in enumerate(SEMANTIC_DIMENSIONS):
        ax = fig.add_subplot(grid[index])
        _draw_remaining_row(
            ax,
            full,
            mapping,
            dimension,
            show_low_support_n=index == 0,
            show_x_labels=index == len(SEMANTIC_DIMENSIONS) - 1,
        )

    country_handles = [
        Patch(facecolor=NSF_COLOR, edgecolor="none", label="NSF"),
        Patch(facecolor=NSFC_COLOR, edgecolor="none", label="NSFC"),
        Patch(facecolor="white", edgecolor="#4E5963", linewidth=0.8, linestyle=(0, (1.2, 1.2)), label="0<n<30"),
    ]
    fig.legend(
        handles=country_handles,
        loc="upper center",
        bbox_to_anchor=(0.54, 0.989),
        ncol=3,
        frameon=False,
        fontsize=5.6,
        handlelength=1.0,
        columnspacing=0.9,
    )
    fig.text(
        0.095,
        0.944,
        "Full decomposition of Other · country colours match Figure 1a; darker = higher pooled rank",
        ha="left",
        va="center",
        fontsize=5.8,
        color="#56616B",
    )
    return fig


def export_figure(fig: plt.Figure, directory: Path, stem: str) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = [
        directory / f"{stem}_preview.png",
        directory / f"{stem}.svg",
        directory / f"{stem}.pdf",
        directory / f"{stem}.tiff",
    ]
    fig.savefig(paths[0], dpi=300, bbox_inches="tight")
    fig.savefig(paths[1], bbox_inches="tight")
    fig.savefig(paths[2], bbox_inches="tight")
    fig.savefig(paths[3], dpi=600, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
    return paths






def main():
    root = Path(__file__).resolve().parents[1]
    data = root / 'data'
    configure_matplotlib()
    annual = pd.read_csv(data/'Supplementary_Fig_2_source_data.csv')
    main = pd.read_csv(data/'Supplementary_Fig_2_semantic_composition.csv')
    mapping = pd.read_csv(data/'Supplementary_Fig_2_code_mapping.csv')
    fig = draw_main_figure(annual, main, mapping)
    export_figure(fig, root/'outputs', 'Supplementary_Fig_2_source_renderer_output')
    plt.close(fig)

if __name__ == '__main__': main()
