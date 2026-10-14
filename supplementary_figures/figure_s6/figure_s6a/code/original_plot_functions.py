from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Mapping

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_hex, to_rgb
from matplotlib.lines import Line2D
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MplPath


CLASS_ORDER = (
    "Relative lower research supply",
    "Near alignment",
    "Relative higher research supply",
)

NSF_COLOR = "#003366"
NSFC_COLOR = "#8B0000"
NEUTRAL_COLOR = "#8A949E"
TEXT_COLOR = "#1F2933"
GRID_COLOR = "#E8ECEF"
LIGHT_BACKGROUND = "#F7F9FA"
AGENCY_COLORS = {"NSF": NSF_COLOR, "NSFC": NSFC_COLOR}

K_ORDER = tuple(f"K{i:02d}" for i in range(1, 7))
A_ORDER = tuple(f"A{i:02d}" for i in range(1, 8))
# Keep the flow-node labels aligned with the canonical codes in the source
# data. Full task/stage definitions belong in the caption or codebook; using
# short prose here could be mistaken for the verbatim source labels.
K_LABELS = {code: code for code in K_ORDER}
A_LABELS = {code: code for code in A_ORDER}

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 7.0,
        "axes.titlesize": 7.0,
        "axes.labelsize": 6.5,
        "xtick.labelsize": 5.8,
        "ytick.labelsize": 5.8,
        "legend.fontsize": 5.6,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "legend.frameon": False,
    }
)

TARGET_SHORT = {
    "3.4": "NCD health",
    "3.6": "Road safety",
    "3.9": "Pollution health",
    "7.1": "Energy access",
    "7.2": "Renewable energy",
    "7.3": "Energy efficiency",
    "9.1": "Infrastructure",
    "9.4": "Industry transition",
    "10.2": "Social inclusion",
    "10.3": "Equal opportunity",
    "11.2": "Urban transport",
    "11.3": "Urbanization",
    "11.5": "Disaster losses",
    "11.6": "Urban impact",
    "13.1": "Climate resilience",
    "13.2": "Climate policy",
    "16.6": "Institutions",
    "16.7": "Inclusive decisions",
    "17.6": "Science cooperation",
    "17.14": "Policy coherence",
    "17.16": "Global partnership",
    "17.17": "Public/civil",
    "17.18": "Data capacity",
}


def classify_mismatch(value: float, threshold: float = 0.5) -> str:
    if value <= -threshold:
        return CLASS_ORDER[0]
    if value >= threshold:
        return CLASS_ORDER[2]
    return CLASS_ORDER[1]


def choose_targets(
    counts: Mapping[str, float],
    coverage: float = 0.85,
    minimum: int = 2,
    maximum: int = 4,
) -> tuple[list[str], float, float]:
    ordered = sorted(
        ((str(code), float(value)) for code, value in counts.items() if float(value) > 0),
        key=lambda item: (-item[1], item[0]),
    )
    total = sum(value for _, value in ordered)
    if total <= 0:
        return [], 0.0, 0.0
    selected: list[str] = []
    selected_support = 0.0
    for code, value in ordered:
        if len(selected) >= maximum:
            break
        selected.append(code)
        selected_support += value
        if len(selected) >= minimum and selected_support / total >= coverage:
            break
    other = total - selected_support
    return selected, other, selected_support / total


def select_sdg_diagnostics(
    mismatch: pd.DataFrame,
    component: pd.DataFrame,
) -> pd.DataFrame:
    left = mismatch.copy()
    if "agency" not in left.columns and "country" in left.columns:
        left = left.rename(columns={"country": "agency"})
    right = component.copy()
    if "agency" not in right.columns and "country" in right.columns:
        right = right.rename(columns={"country": "agency"})
    left["M_count"] = left["clr_supply_count"].astype(float) - left["clr_challenge"].astype(float)
    left["mismatch_class"] = left["M_count"].map(classify_mismatch)
    merged = left.merge(
        right[["agency", "sdg", "contribution_share_count"]],
        on=["agency", "sdg"],
        how="left",
        validate="one_to_one",
    )
    merged["contribution_share_count"] = merged["contribution_share_count"].astype(float)
    merged["diagnostic_status"] = "Diagnostic count-only; stability gate unresolved"
    selected = (
        merged.sort_values(
            ["agency", "mismatch_class", "contribution_share_count", "sdg"],
            ascending=[True, True, False, True],
        )
        .groupby(["agency", "mismatch_class"], observed=True, as_index=False)
        .head(2)
        .copy()
    )
    return selected.sort_values(["agency", "mismatch_class", "sdg"]).reset_index(drop=True)


def _valid_codes(values: object) -> list[str]:
    if not isinstance(values, (list, tuple, set)):
        return []
    return [str(value) for value in dict.fromkeys(values) if str(value)]


def build_joint_paths(
    projects: Mapping[str, pd.DataFrame],
    selected: pd.DataFrame,
    target_labels: Mapping[str, str],
    coverage: float = 0.85,
    minimum_targets: int = 2,
    maximum_targets: int = 4,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected_map = {
        agency: dict(zip(frame["sdg"].astype(str), frame["mismatch_class"].astype(str)))
        for agency, frame in selected.groupby("agency", observed=True)
    }
    target_counts: defaultdict[tuple[str, str, str], float] = defaultdict(float)
    for agency, data in projects.items():
        agency_selected = selected_map.get(agency, {})
        for sdgs, targets, family_weight in data[
            ["sdg_codes", "target_codes", "project_family_weight"]
        ].itertuples(index=False, name=None):
            sdg_codes = _valid_codes(sdgs)
            target_codes = _valid_codes(targets)
            if not sdg_codes:
                continue
            sdg_weight = float(family_weight) / len(sdg_codes)
            for sdg in (code for code in sdg_codes if code in agency_selected):
                prefix = f"{int(sdg[1:])}."
                relevant = [code for code in target_codes if code.startswith(prefix)]
                if not relevant:
                    continue
                for target in relevant:
                    target_counts[(agency, sdg, target)] += sdg_weight / len(relevant)

    chosen_map: dict[tuple[str, str], set[str]] = {}
    target_audit_rows: list[dict[str, object]] = []
    for agency, frame in selected.groupby("agency", observed=True):
        for sdg in frame["sdg"].astype(str):
            counts = {
                target: support
                for (a, goal, target), support in target_counts.items()
                if a == agency and goal == sdg
            }
            chosen, other_support, achieved = choose_targets(
                counts,
                coverage=coverage,
                minimum=minimum_targets,
                maximum=maximum_targets,
            )
            chosen_map[(agency, sdg)] = set(chosen)
            total = sum(counts.values())
            for target, support in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
                target_audit_rows.append(
                    {
                        "agency": agency,
                        "sdg": sdg,
                        "target": target,
                        "target_full_label": target_labels.get(target, ""),
                        "target_short_label": TARGET_SHORT.get(target, target),
                        "target_support": support,
                        "target_share_within_sdg": support / total if total else np.nan,
                        "displayed_individually": target in chosen,
                        "display_target": target if target in chosen else f"{sdg}:Other",
                        "selected_target_coverage": achieved,
                        "other_target_support": other_support,
                    }
                )

    path_counts: defaultdict[tuple[str, str, str, str, str, str], float] = defaultdict(float)
    for agency, data in projects.items():
        agency_selected = selected_map.get(agency, {})
        required = [
            "sdg_codes",
            "target_codes",
            "primary_knowledge_codes",
            "action_codes",
            "project_family_weight",
        ]
        for sdgs, targets, knowledge, actions, family_weight in data[required].itertuples(index=False, name=None):
            sdg_codes = _valid_codes(sdgs)
            target_codes = _valid_codes(targets)
            knowledge_codes = _valid_codes(knowledge)
            action_codes = _valid_codes(actions)
            if not sdg_codes or not knowledge_codes or not action_codes:
                continue
            sdg_weight = float(family_weight) / len(sdg_codes)
            for sdg in (code for code in sdg_codes if code in agency_selected):
                prefix = f"{int(sdg[1:])}."
                relevant = [code for code in target_codes if code.startswith(prefix)]
                if not relevant:
                    continue
                target_weight = sdg_weight / len(relevant)
                for raw_target in relevant:
                    display_target = (
                        raw_target
                        if raw_target in chosen_map.get((agency, sdg), set())
                        else f"{sdg}:Other"
                    )
                    for knowledge_task in knowledge_codes:
                        for action_stage in action_codes:
                            path_counts[
                                (
                                    agency,
                                    agency_selected[sdg],
                                    sdg,
                                    display_target,
                                    knowledge_task,
                                    action_stage,
                                )
                            ] += target_weight / len(knowledge_codes) / len(action_codes)

    path_rows = [
        {
            "agency": agency,
            "mismatch_class": mismatch_class,
            "sdg": sdg,
            "target": target,
            "target_short_label": (
                "Other targets"
                if target.endswith(":Other")
                else TARGET_SHORT.get(target, target)
            ),
            "target_full_label": (
                "Aggregated formal Targets outside the adaptive display set"
                if target.endswith(":Other")
                else target_labels.get(target, "")
            ),
            "knowledge_task": knowledge_task,
            "action_stage": action_stage,
            "fractional_project_support": support,
            "path_code": f"{sdg}→{target.split(':')[-1]}→{knowledge_task}→{action_stage}",
        }
        for (
            agency,
            mismatch_class,
            sdg,
            target,
            knowledge_task,
            action_stage,
        ), support in path_counts.items()
    ]
    paths = pd.DataFrame(path_rows)
    target_audit = pd.DataFrame(target_audit_rows)
    if not paths.empty:
        paths = paths.sort_values(
            ["agency", "mismatch_class", "sdg", "target", "knowledge_task", "action_stage"]
        ).reset_index(drop=True)
    return paths, target_audit


ACTION_GROUPS = {
    "A01": "Knowledge and methods",
    "A02": "Knowledge and methods",
    "A03": "Testing and validation",
    "A04": "Testing and validation",
    "A05": "Decision, scaling and evaluation",
    "A06": "Decision, scaling and evaluation",
    "A07": "Decision, scaling and evaluation",
}
ACTION_GROUP_ORDER = (
    "Knowledge and methods",
    "Testing and validation",
    "Decision, scaling and evaluation",
)


def summarize_classes(paths: pd.DataFrame) -> pd.DataFrame:
    summary = (
        paths.groupby(["agency", "mismatch_class"], observed=True, as_index=False)[
            "fractional_project_support"
        ]
        .sum()
        .sort_values(["agency", "mismatch_class"])
        .reset_index(drop=True)
    )
    agency_total = summary.groupby("agency", observed=True)["fractional_project_support"].transform("sum")
    summary["share_of_selected_support"] = summary["fractional_project_support"] / agency_total
    return summary


def summarize_actions(paths: pd.DataFrame) -> pd.DataFrame:
    work = paths.copy()
    work["action_group"] = work["action_stage"].map(ACTION_GROUPS)
    if work["action_group"].isna().any():
        missing = sorted(work.loc[work["action_group"].isna(), "action_stage"].astype(str).unique())
        raise ValueError(f"Unknown action stages: {missing}")
    grouped = work.groupby(
        ["agency", "mismatch_class", "action_group"],
        observed=True,
        as_index=False,
    )["fractional_project_support"].sum()
    panel_keys = work[["agency", "mismatch_class"]].drop_duplicates()
    full = panel_keys.merge(pd.DataFrame({"action_group": ACTION_GROUP_ORDER}), how="cross")
    full = full.merge(grouped, on=["agency", "mismatch_class", "action_group"], how="left")
    full["fractional_project_support"] = full["fractional_project_support"].fillna(0.0)
    class_total = full.groupby(["agency", "mismatch_class"], observed=True)[
        "fractional_project_support"
    ].transform("sum")
    full["share_within_class"] = np.divide(
        full["fractional_project_support"],
        class_total,
        out=np.zeros(len(full), dtype=float),
        where=class_total.to_numpy(dtype=float) > 0,
    )
    full["action_group"] = pd.Categorical(
        full["action_group"], categories=ACTION_GROUP_ORDER, ordered=True
    )
    return full.sort_values(["agency", "mismatch_class", "action_group"]).reset_index(drop=True)


def summarize_target_coverage(target_audit: pd.DataFrame) -> pd.DataFrame:
    work = target_audit.copy()
    work["displayed_support"] = np.where(
        work["displayed_individually"].astype(bool), work["target_support"].astype(float), 0.0
    )
    summary = work.groupby(["agency", "sdg"], observed=True, as_index=False).agg(
        target_support=("target_support", "sum"),
        displayed_target_support=("displayed_support", "sum"),
        total_target_n=("target", "nunique"),
        displayed_target_n=("displayed_individually", "sum"),
    )
    summary["other_target_support"] = summary["target_support"] - summary["displayed_target_support"]
    summary["displayed_target_coverage"] = summary["displayed_target_support"] / summary["target_support"]
    summary["other_target_share"] = summary["other_target_support"] / summary["target_support"]
    return summary


def attach_target_coverage(target_audit: pd.DataFrame) -> pd.DataFrame:
    summary = summarize_target_coverage(target_audit)
    enrichment = summary.drop(columns=["target_support"])
    return target_audit.merge(
        enrichment,
        on=["agency", "sdg"],
        how="left",
        validate="many_to_one",
    )


def validate_mass_conservation(
    paths: pd.DataFrame,
    target_audit: pd.DataFrame,
    tolerance: float = 1e-10,
) -> dict[str, object]:
    path_mass = paths.groupby(["agency", "sdg"], observed=True)[
        "fractional_project_support"
    ].sum()
    target_mass = target_audit.groupby(["agency", "sdg"], observed=True)["target_support"].sum()
    comparison = pd.concat(
        [path_mass.rename("path_mass"), target_mass.rename("target_mass")], axis=1
    ).fillna(0.0)
    comparison["absolute_error"] = (comparison["path_mass"] - comparison["target_mass"]).abs()
    max_error = float(comparison["absolute_error"].max()) if len(comparison) else 0.0
    nonnegative = bool((paths["fractional_project_support"].astype(float) >= 0).all())
    return {
        "passed": bool(max_error <= tolerance and nonnegative),
        "max_sdg_mass_error": max_error,
        "nonnegative_paths": nonnegative,
        "comparison": comparison.reset_index(),
    }


def _blend(color: str, white_fraction: float) -> str:
    rgb = np.array(to_rgb(color), dtype=float)
    mixed = rgb * (1.0 - white_fraction) + np.ones(3) * white_fraction
    return to_hex(mixed)


def _ribbon(
    ax: plt.Axes,
    x0: float,
    x1: float,
    y0_low: float,
    y0_high: float,
    y1_low: float,
    y1_high: float,
    color: str,
    alpha: float,
) -> None:
    control = (x1 - x0) * 0.42
    vertices = [
        (x0, y0_low),
        (x0 + control, y0_low),
        (x1 - control, y1_low),
        (x1, y1_low),
        (x1, y1_high),
        (x1 - control, y1_high),
        (x0 + control, y0_high),
        (x0, y0_high),
        (x0, y0_low),
    ]
    codes = [
        MplPath.MOVETO,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.LINETO,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CLOSEPOLY,
    ]
    ax.add_patch(
        PathPatch(
            MplPath(vertices, codes),
            facecolor=color,
            edgecolor="none",
            alpha=alpha,
            zorder=1,
        )
    )


def _node_orders(part: pd.DataFrame) -> list[list[str]]:
    sdg_support = part.groupby("sdg", observed=True)["fractional_project_support"].sum()
    sdgs = sorted(sdg_support.index.astype(str), key=lambda value: int(value[1:]))
    target_support = (
        part.groupby(["sdg", "target"], observed=True)["fractional_project_support"]
        .sum()
        .reset_index()
    )
    targets: list[str] = []
    for sdg in sdgs:
        block = target_support.loc[target_support["sdg"].eq(sdg)].copy()
        block["other"] = block["target"].astype(str).str.endswith(":Other")
        block = block.sort_values(["other", "fractional_project_support", "target"], ascending=[True, False, True])
        targets.extend(block["target"].astype(str).tolist())
    knowledge = [code for code in K_ORDER if code in set(part["knowledge_task"].astype(str))]
    actions = [code for code in A_ORDER if code in set(part["action_stage"].astype(str))]
    return [sdgs, targets, knowledge, actions]


def _node_bounds(
    part: pd.DataFrame,
    orders: list[list[str]],
    lower: float = 0.18,
    upper: float = 0.88,
) -> tuple[dict[tuple[int, str], tuple[float, float]], float]:
    layer_columns = ["sdg", "target", "knowledge_task", "action_stage"]
    total = float(part["fractional_project_support"].sum())
    max_nodes = max(max(len(order), 1) for order in orders)
    gap = min(0.010, 0.11 / max_nodes)
    scale = (upper - lower - gap * (max_nodes - 1)) / total if total > 0 else 0.0
    bounds: dict[tuple[int, str], tuple[float, float]] = {}
    for layer_index, (column, order) in enumerate(zip(layer_columns, orders)):
        totals = part.groupby(column, observed=True)["fractional_project_support"].sum()
        occupied = total * scale + gap * max(len(order) - 1, 0)
        cursor = lower + (upper - lower - occupied) / 2.0
        for node in order:
            height = float(totals.get(node, 0.0)) * scale
            bounds[(layer_index, node)] = (cursor, cursor + height)
            cursor += height + gap
    return bounds, scale


def _path_intervals(
    part: pd.DataFrame,
    orders: list[list[str]],
    bounds: dict[tuple[int, str], tuple[float, float]],
    scale: float,
) -> dict[tuple[int, int], tuple[float, float]]:
    layer_columns = ["sdg", "target", "knowledge_task", "action_stage"]
    work = part.sort_values(layer_columns).reset_index(drop=True)
    intervals: dict[tuple[int, int], tuple[float, float]] = {}
    for layer_index, column in enumerate(layer_columns):
        cursor = {node: bounds[(layer_index, node)][0] for node in orders[layer_index]}
        for row_index, row in work.iterrows():
            node = str(row[column])
            height = float(row["fractional_project_support"]) * scale
            start = cursor[node]
            intervals[(layer_index, row_index)] = (start, start + height)
            cursor[node] += height
    return intervals


def _target_display_label(part: pd.DataFrame, target: str) -> str:
    if target.endswith(":Other"):
        target_support = float(
            part.loc[part["target"].eq(target), "fractional_project_support"].sum()
        )
        sdg = target.split(":")[0]
        sdg_support = float(part.loc[part["sdg"].eq(sdg), "fractional_project_support"].sum())
        share = target_support / sdg_support if sdg_support else 0.0
        return f"SDG{sdg[1:]} other ({share:.0%})"
    return target


def spread_positions(
    positions: list[float],
    lower: float,
    upper: float,
    minimum_gap: float,
) -> list[float]:
    if not positions:
        return []
    values = np.sort(np.asarray(positions, dtype=float))
    if len(values) == 1:
        return [float(np.clip(values[0], lower, upper))]
    feasible_gap = min(float(minimum_gap), (upper - lower) / (len(values) - 1))
    values[0] = max(values[0], lower)
    for index in range(1, len(values)):
        values[index] = max(values[index], values[index - 1] + feasible_gap)
    if values[-1] > upper:
        values -= values[-1] - upper
    for index in range(len(values) - 2, -1, -1):
        values[index] = min(values[index], values[index + 1] - feasible_gap)
    if values[0] < lower:
        values += lower - values[0]
    return values.tolist()


def draw_alluvial_panel(
    ax: plt.Axes,
    paths: pd.DataFrame,
    agency: str,
    class_name: str,
    show_headers: bool = False,
) -> None:
    part = paths.loc[
        paths["agency"].eq(agency) & paths["mismatch_class"].eq(class_name)
    ].copy()
    ax.set_facecolor("none")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(-0.08, 1.13)
    ax.set_ylim(0, 1)
    if part.empty:
        ax.text(0.5, 0.5, "No eligible paths", ha="center", va="center", color=NEUTRAL_COLOR)
        return

    x_positions = [0.02, 0.32, 0.63, 0.94]
    layer_names = ["SDG", "Formal Target", "Knowledge task", "Research–action stage"]
    orders = _node_orders(part)
    bounds, scale = _node_bounds(part, orders)
    work = part.sort_values(["sdg", "target", "knowledge_task", "action_stage"]).reset_index(drop=True)
    intervals = _path_intervals(work, orders, bounds, scale)
    sdgs = orders[0]
    sdg_colors = {
        sdg: (AGENCY_COLORS[agency] if index % 2 == 0 else
              {"NSF": "#7F99B2", "NSFC": "#C57F7F"}[agency])
        for index, sdg in enumerate(sdgs)
    }
    top_indices = set(work.nlargest(min(2, len(work)), "fractional_project_support").index.tolist())
    for row_index, row in work.iterrows():
        color = sdg_colors[str(row["sdg"])]
        alpha = 0.62
        for layer_index in range(3):
            source = intervals[(layer_index, row_index)]
            target = intervals[(layer_index + 1, row_index)]
            _ribbon(
                ax,
                x_positions[layer_index] + 0.008,
                x_positions[layer_index + 1] - 0.008,
                source[0],
                source[1],
                target[0],
                target[1],
                color,
                alpha,
            )

    node_fills = ["#ECEFF1", "#ECEFF1", "#E4EDF5", "#ECEFF1"]
    node_width = 0.012
    layer_columns = ["sdg", "target", "knowledge_task", "action_stage"]
    for layer_index, (column, order) in enumerate(zip(layer_columns, orders)):
        x = x_positions[layer_index]
        if show_headers:
            ax.text(x, 0.985, layer_names[layer_index], ha="center", va="top", fontsize=5.7, fontweight="bold", color=TEXT_COLOR)
        centers = [(bounds[(layer_index, node)][0] + bounds[(layer_index, node)][1]) / 2 for node in order]
        if layer_index == 0:
            label_positions = centers
        else:
            gap_by_layer = {1: 0.052, 2: 0.068, 3: 0.060}
            label_positions = spread_positions(centers, 0.20, 0.86, gap_by_layer[layer_index])
        label_y = dict(zip(order, label_positions))
        for node in order:
            y0, y1 = bounds[(layer_index, node)]
            face = node_fills[layer_index]
            if layer_index == 0:
                face = {"NSF": "#E4EDF5", "NSFC": "#F6E4E4"}[agency]
            if layer_index == 1 and node.endswith(":Other"):
                face = _blend(NEUTRAL_COLOR, 0.55)
            if layer_index == 3:
                action_index = A_ORDER.index(node)
                face = _blend("#64727D", 0.78 - action_index * 0.07)
            ax.add_patch(
                Rectangle(
                    (x - node_width / 2, y0),
                    node_width,
                    max(y1 - y0, 0.0015),
                    facecolor=face,
                    edgecolor=TEXT_COLOR,
                    linewidth=0.35,
                    zorder=3,
                )
            )
            if layer_index == 0:
                label = node.replace("S", "SDG")
                tx, ha = x - 0.010, "right"
            elif layer_index == 1:
                label = _target_display_label(part, node)
                tx, ha = x + 0.010, "left"
            elif layer_index == 2:
                label = K_LABELS.get(node, node)
                tx, ha = x + 0.010, "left"
            else:
                label = A_LABELS.get(node, node)
                tx, ha = x + 0.010, "left"
            center_y = (y0 + y1) / 2
            text_y = label_y[node]
            if layer_index > 0 and abs(text_y - center_y) > 0.004:
                ax.plot(
                    [x + node_width / 2, tx - 0.002],
                    [center_y, text_y],
                    color="#A9B1B8",
                    linewidth=0.28,
                    zorder=3.5,
                )
            ax.text(tx, text_y, label, ha=ha, va="center", fontsize=5.0, color=TEXT_COLOR, zorder=4)

def draw_action_summary(ax: plt.Axes, action_summary: pd.DataFrame) -> None:
    group_colors = {
        "Knowledge and methods": "#D9DEE3",
        "Testing and validation": "#8A949E",
        "Decision, scaling and evaluation": "#59636E",
    }
    y_base = np.arange(len(CLASS_ORDER))[::-1]
    offsets = {"NSF": 0.17, "NSFC": -0.17}
    for agency in ("NSF", "NSFC"):
        for class_index, class_name in enumerate(CLASS_ORDER):
            block = action_summary.loc[
                action_summary["agency"].eq(agency)
                & action_summary["mismatch_class"].eq(class_name)
            ].copy()
            shares = {str(row.action_group): float(row.share_within_class) for row in block.itertuples(index=False)}
            left = 0.0
            y = y_base[class_index] + offsets[agency]
            for group in ACTION_GROUP_ORDER:
                width = shares.get(group, 0.0) * 100
                ax.barh(
                    y,
                    width,
                    left=left,
                    height=0.25,
                    color=group_colors[group],
                    edgecolor=AGENCY_COLORS[agency],
                    linewidth=0.65,
                )
                if width >= 7:
                    ax.text(left + width / 2, y, f"{width:.0f}%", ha="center", va="center", fontsize=5.0, color=TEXT_COLOR)
                left += width
            ax.text(-1.5, y, agency, ha="right", va="center", fontsize=5.0, color=AGENCY_COLORS[agency], fontweight="bold")
    ax.set_xlim(-11, 100)
    ax.set_yticks(y_base, ["Lower", "Near", "Higher"])
    ax.set_xlabel("Share of selected paths within mismatch class (%)", labelpad=1)
    ax.set_title("Action-stage reach of selected content paths", loc="left", fontsize=6.2, fontweight="bold", pad=2)
    ax.grid(axis="x", color=GRID_COLOR, linewidth=0.45)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)


def render_figure(
    paths: pd.DataFrame,
    selected: pd.DataFrame,
    class_summary: pd.DataFrame,
    action_summary: pd.DataFrame,
) -> plt.Figure:
    del selected, class_summary
    fig = plt.figure(figsize=(7.2, 5.0), facecolor="white")
    grid = fig.add_gridspec(4, 2, height_ratios=[1.0, 1.0, 1.0, 0.82], hspace=0.24, wspace=0.09)
    axes: dict[tuple[int, str], plt.Axes] = {}
    for row_index, class_name in enumerate(CLASS_ORDER):
        for column_index, agency in enumerate(("NSF", "NSFC")):
            ax = fig.add_subplot(grid[row_index, column_index])
            draw_alluvial_panel(ax, paths, agency, class_name, show_headers=row_index == 0)
            axes[(row_index, agency)] = ax
        axes[(row_index, "NSF")].text(
            -0.075,
            1.035,
            class_name,
            transform=axes[(row_index, "NSF")].transAxes,
            ha="left",
            va="bottom",
            fontsize=5.6,
            color=TEXT_COLOR,
            fontweight="bold",
        )
    summary_ax = fig.add_subplot(grid[3, :])
    draw_action_summary(summary_ax, action_summary)

    fig.text(0.015, 0.982, "b", fontsize=10.5, fontweight="bold", va="top", color="black")
    fig.text(
        0.055,
        0.978,
        "Internal organization of SDG supply–challenge mismatch",
        fontsize=9.0,
        fontweight="bold",
        va="top",
        color=TEXT_COLOR,
    )
    fig.text(
        0.055,
        0.951,
        "Selected SDGs → formal Targets → knowledge tasks → research–action stages",
        fontsize=5.9,
        color="#68747E",
        va="top",
    )
    fig.text(0.985, 0.978, "Diagnostic count-only", ha="right", va="top", fontsize=5.3, color="#8A949E", fontstyle="italic")
    fig.text(0.27, 0.918, "NSF", ha="center", va="bottom", fontsize=8.0, fontweight="bold", color=NSF_COLOR)
    fig.text(0.74, 0.918, "NSFC", ha="center", va="bottom", fontsize=8.0, fontweight="bold", color=NSFC_COLOR)

    flow_handles = [
        Line2D([], [], color=NSF_COLOR, linewidth=4, alpha=0.62, label="NSF"),
        Line2D([], [], color=NSFC_COLOR, linewidth=4, alpha=0.62, label="NSFC"),
    ]
    action_handles = [
        Rectangle((0, 0), 1, 1, facecolor="#D9DEE3", edgecolor="none", label="A01–A02"),
        Rectangle((0, 0), 1, 1, facecolor="#8A949E", edgecolor="none", label="A03–A04"),
        Rectangle((0, 0), 1, 1, facecolor="#59636E", edgecolor="none", label="A05–A07"),
    ]
    flow_legend = fig.legend(
        handles=flow_handles,
        title="Flow width = fractional project support",
        loc="lower left",
        bbox_to_anchor=(0.055, 0.004),
        ncol=2,
        frameon=False,
        columnspacing=0.9,
        handletextpad=0.45,
        fontsize=5.0,
    )
    flow_legend.get_title().set_fontsize(5.0)
    flow_legend.get_title().set_color(TEXT_COLOR)
    action_legend = fig.legend(
        handles=action_handles,
        title="Action-stage groups",
        loc="lower right",
        bbox_to_anchor=(0.975, 0.004),
        ncol=3,
        frameon=False,
        columnspacing=0.75,
        handletextpad=0.35,
        fontsize=5.0,
    )
    action_legend.get_title().set_fontsize(5.0)
    action_legend.get_title().set_color(TEXT_COLOR)
    fig.subplots_adjust(left=0.055, right=0.975, top=0.895, bottom=0.118)
    return fig


def save_exports(fig: plt.Figure, output_stem: Path, dpi: int = 600) -> list[Path]:
    output_stem = Path(output_stem)
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    paths = [output_stem.with_suffix(extension) for extension in (".svg", ".pdf", ".png", ".tiff")]
    fig.savefig(paths[0], bbox_inches="tight")
    fig.savefig(paths[1], bbox_inches="tight")
    fig.savefig(paths[2], dpi=dpi, bbox_inches="tight", facecolor="white")
    fig.savefig(paths[3], dpi=dpi, bbox_inches="tight", facecolor="white")
    return paths


def write_data_outputs(
    output_root: Path,
    selected: pd.DataFrame,
    paths: pd.DataFrame,
    target_audit: pd.DataFrame,
    class_summary: pd.DataFrame,
    action_summary: pd.DataFrame,
    provenance: str,
) -> list[Path]:
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    outputs: list[tuple[str, object]] = [
        ("Supplementary_Fig_6a_入选SDG诊断.csv", selected),
        ("Supplementary_Fig_6a_Target覆盖审计.csv", target_audit),
        ("Supplementary_Fig_6a_完整联合路径.csv", paths),
        ("Supplementary_Fig_6a_偏离类别汇总.csv", class_summary),
        ("Supplementary_Fig_6a_行动阶段汇总.csv", action_summary),
        ("Supplementary_Fig_6a_数据来源说明.txt", provenance),
    ]
    written: list[Path] = []
    for filename, payload in outputs:
        path = output_root / filename
        if isinstance(payload, pd.DataFrame):
            payload.to_csv(path, index=False, encoding="utf-8-sig")
        else:
            path.write_text(str(payload), encoding="utf-8")
        written.append(path)
    return written


