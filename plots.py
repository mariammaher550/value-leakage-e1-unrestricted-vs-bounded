#!/usr/bin/env python3
"""Regenerate E1 bias, distribution, and reasoning-trajectory figures from saved files."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from fractions import Fraction
from pathlib import Path
from typing import Any

from e1lib import CONDITIONS, FORMATS, ROOT, load_config, load_tasks, read_jsonl, record_fraction, run_dir, validate_tasks_file, write_json

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


COLORS = {"unrestricted": "#2563EB", "bounded": "#E11D48"}
CONDITION_COLORS = {"baseline": "#64748B", "above_good": "#16A34A", "below_good": "#EA580C"}


def _save_figure(fig: plt.Figure, base_path: Path) -> None:
    base_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(base_path.with_suffix(".png"), dpi=220, bbox_inches="tight")
    fig.savefig(base_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        if not fields:
            return
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def plot_bias_by_question(metrics: dict[str, Any], output_dir: Path) -> None:
    tasks = list(dict.fromkeys(row["task"] for row in metrics["per_task"]))
    x = np.arange(len(tasks), dtype=float)
    fig, ax = plt.subplots(figsize=(max(7, len(tasks) * 1.05), 4.8))
    width = 0.32
    for offset, fmt in ((-width / 2, "unrestricted"), (width / 2, "bounded")):
        fmt_rows = {row["task"]: row for row in metrics["per_task"] if row["format"] == fmt}
        values = np.asarray(
            [fmt_rows[task]["bias"] if fmt_rows[task]["bias"] is not None else np.nan for task in tasks]
        )
        low = np.asarray(
            [fmt_rows[task]["ci_low"] if fmt_rows[task]["ci_low"] is not None else np.nan for task in tasks]
        )
        high = np.asarray(
            [fmt_rows[task]["ci_high"] if fmt_rows[task]["ci_high"] is not None else np.nan for task in tasks]
        )
        valid = np.isfinite(values)
        errors = np.vstack([values - low, high - values])[:, valid]
        ax.errorbar(
            x[valid] + offset,
            values[valid],
            yerr=errors,
            fmt="o",
            capsize=3,
            color=COLORS[fmt],
            label=fmt.capitalize(),
        )
    ax.axhline(0, color="black", linewidth=0.9)
    ax.set_xticks(x, tasks, rotation=35, ha="right")
    ax.set_ylabel("Bias (−1 reversed, +1 favored)")
    ax.set_ylim(-1.08, 1.08)
    ax.set_title("Donation-bet bias by question and estimate format")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.2)
    _save_figure(fig, output_dir / "bias_by_question")
    _write_csv(output_dir / "plot_data" / "bias_by_question.csv", metrics["per_task"])


def plot_overall(metrics: dict[str, Any], output_dir: Path) -> None:
    desired = [
        ("overall_signed_bias", "unrestricted", "Unrestricted bias", COLORS["unrestricted"]),
        ("overall_signed_bias", "bounded", "Bounded bias", COLORS["bounded"]),
        (
            "mean_task_delta_bias_bounded_minus_unrestricted",
            "comparison",
            "Bounded − unrestricted",
            "#7C3AED",
        ),
    ]
    lookup = {(row["metric"], row["format"]): row for row in metrics["overall"]}
    plotted = [(label, color, lookup[(metric, fmt)]) for metric, fmt, label, color in desired]
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    for position, (label, color, row) in enumerate(plotted):
        if row["value"] is None:
            continue
        value = float(row["value"])
        error = np.asarray([[value - float(row["ci_low"])], [float(row["ci_high"]) - value]])
        ax.errorbar(position, value, yerr=error, fmt="o", color=color, capsize=5, markersize=8)
    ax.axhline(0, color="black", linewidth=0.9)
    ax.set_xticks(range(len(plotted)), [item[0] for item in plotted], rotation=15, ha="right")
    ax.set_ylabel("Bias units")
    ax.set_ylim(-1.1, 1.1)
    ax.set_title("Overall bias and bounded-format difference")
    ax.grid(axis="y", alpha=0.2)
    _save_figure(fig, output_dir / "overall_bias_and_difference")
    _write_csv(output_dir / "plot_data" / "overall_bias.csv", metrics["overall"])


def plot_distributions(
    judged: list[dict[str, Any]],
    thresholds: dict[str, Any],
    tasks: dict[str, Any],
    output_dir: Path,
) -> None:
    plotted_rows: list[dict[str, Any]] = []
    for task, threshold_record in thresholds.get("tasks", {}).items():
        threshold = float(record_fraction(threshold_record))
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
        task_values: list[float] = []
        for ax, fmt in zip(axes, FORMATS, strict=True):
            groups: list[list[float]] = []
            for condition in CONDITIONS:
                cell_rows = [
                    row
                    for row in judged
                    if row.get("task") == task
                    and row.get("format") == fmt
                    and row.get("condition") == condition
                    and isinstance(row.get("final_estimate"), int)
                    and not isinstance(row.get("final_estimate"), bool)
                ]
                values = [float(row["final_estimate"]) for row in cell_rows]
                groups.append(values)
                task_values.extend(values)
                for row in cell_rows:
                    plotted_rows.append(
                        {
                            "sample_id": row["sample_id"],
                            "task": task,
                            "format": fmt,
                            "condition": condition,
                            "final_estimate": row["final_estimate"],
                            "threshold": threshold,
                            "lower_bound": row.get("lower_bound"),
                            "upper_bound": row.get("upper_bound"),
                            "bound_violation": row.get("bound_violation", False),
                        }
                    )
            nonempty_positions = [position + 1 for position, values in enumerate(groups) if values]
            nonempty_groups = [values for values in groups if values]
            if nonempty_groups:
                boxes = ax.boxplot(
                    nonempty_groups,
                    positions=nonempty_positions,
                    widths=0.5,
                    patch_artist=True,
                    showfliers=False,
                )
                for patch, position in zip(boxes["boxes"], nonempty_positions, strict=True):
                    patch.set_facecolor(CONDITION_COLORS[CONDITIONS[position - 1]])
                    patch.set_alpha(0.22)
                for position, values in zip(nonempty_positions, nonempty_groups, strict=True):
                    jitter = np.linspace(-0.16, 0.16, len(values)) if len(values) > 1 else np.asarray([0.0])
                    ax.scatter(
                        position + jitter,
                        values,
                        s=16,
                        alpha=0.65,
                        color=CONDITION_COLORS[CONDITIONS[position - 1]],
                    )
            ax.axhline(threshold, color="black", linestyle="--", linewidth=1.2, label="tau")
            if fmt == "bounded":
                ax.axhline(threshold_record["lower_bound"], color="#475569", linestyle=":", linewidth=1)
                ax.axhline(threshold_record["upper_bound"], color="#475569", linestyle=":", linewidth=1)
            ax.set_xticks(range(1, 4), [name.replace("_", " ") for name in CONDITIONS], rotation=20)
            ax.set_title(fmt.capitalize())
            ax.grid(axis="y", alpha=0.18)
        positive_values = [value for value in task_values if value > 0]
        spans_orders = bool(positive_values) and max(task_values) / min(positive_values) > 100
        if task_values and (min(task_values) <= 0 or spans_orders):
            axes[0].set_yscale("symlog", linthresh=max(abs(threshold) * 0.01, 1.0))
        axes[0].set_ylabel(f"Final estimate ({tasks[task]['unit']})")
        fig.suptitle(f"Final-estimate distributions: {task}")
        fig.tight_layout()
        _save_figure(fig, output_dir / f"final_estimate_distributions_{task}")
    _write_csv(output_dir / "plot_data" / "final_estimate_distributions.csv", plotted_rows)


def _trajectory_matrix(
    rows: list[dict[str, Any]], threshold: Fraction, grid: np.ndarray
) -> tuple[np.ndarray, list[str]]:
    curves: list[np.ndarray] = []
    identifiers: list[str] = []
    threshold_float = float(threshold)
    for row in rows:
        trajectory = row.get("trajectory")
        if not isinstance(trajectory, list) or len(trajectory) < 2:
            continue
        if any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            for value in trajectory
        ):
            continue
        normalized = (np.asarray(trajectory, dtype=float) - threshold_float) / threshold_float
        positions = np.linspace(0.0, 1.0, len(normalized))
        curves.append(np.interp(grid, positions, normalized))
        identifiers.append(row["sample_id"])
    if not curves:
        return np.empty((0, len(grid))), identifiers
    return np.vstack(curves), identifiers


def plot_trajectories(
    judged: list[dict[str, Any]],
    thresholds: dict[str, Any],
    study: str,
    output_dir: Path,
) -> None:
    grid = np.linspace(0.0, 1.0, 1000)
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True, sharey=True)
    summary_rows: list[dict[str, Any]] = []
    npz_payload: dict[str, np.ndarray] = {"estimate_position": grid}
    mapping: dict[str, list[str]] = {}
    for row_index, fmt in enumerate(FORMATS):
        for column_index, condition in enumerate(CONDITIONS):
            ax = axes[row_index, column_index]
            task_curves: list[np.ndarray] = []
            task_names: list[str] = []
            rollout_matrices: list[np.ndarray] = []
            for task, threshold_record in thresholds.get("tasks", {}).items():
                cell = [
                    row
                    for row in judged
                    if row.get("task") == task
                    and row.get("format") == fmt
                    and row.get("condition") == condition
                ]
                matrix, identifiers = _trajectory_matrix(cell, record_fraction(threshold_record), grid)
                if not len(matrix):
                    continue
                key = f"{fmt}__{condition}__{task}"
                npz_payload[key] = matrix
                mapping[key] = identifiers
                rollout_matrices.append(matrix)
                median_curve = np.median(matrix, axis=0)
                task_curves.append(median_curve)
                task_names.append(task)
                for position, value in zip(grid, median_curve, strict=True):
                    summary_rows.append(
                        {
                            "format": fmt,
                            "condition": condition,
                            "curve_type": "task_median",
                            "task": task,
                            "estimate_position": position,
                            "median": value,
                            "q25": None,
                            "q75": None,
                            "band_label": None,
                        }
                    )
                ax.plot(grid, median_curve, color=CONDITION_COLORS[condition], alpha=0.28, linewidth=1)

            if task_curves:
                stacked_tasks = np.vstack(task_curves)
                aggregate = np.median(stacked_tasks, axis=0)
                if study == "pilot":
                    pooled_rollouts = np.vstack(rollout_matrices)
                    q25, q75 = np.quantile(pooled_rollouts, [0.25, 0.75], axis=0)
                    band_label = "Variation across rollouts"
                else:
                    q25, q75 = np.quantile(stacked_tasks, [0.25, 0.75], axis=0)
                    band_label = "Across-task interquartile band"
                ax.fill_between(
                    grid,
                    q25,
                    q75,
                    color=CONDITION_COLORS[condition],
                    alpha=0.16,
                    label=band_label,
                )
                ax.plot(
                    grid,
                    aggregate,
                    color=CONDITION_COLORS[condition],
                    linewidth=2.3,
                    label="Aggregate median",
                )
                for position, median_value, low, high in zip(grid, aggregate, q25, q75, strict=True):
                    summary_rows.append(
                        {
                            "format": fmt,
                            "condition": condition,
                            "curve_type": "aggregate",
                            "task": "all",
                            "estimate_position": position,
                            "median": median_value,
                            "q25": low,
                            "q75": high,
                            "band_label": band_label,
                        }
                    )
            else:
                ax.text(0.5, 0.5, "No usable trajectories", ha="center", va="center", transform=ax.transAxes)
            ax.axhline(0, color="black", linewidth=0.8)
            ax.set_title(f"{fmt.capitalize()} · {condition.replace('_', ' ')}")
            ax.grid(alpha=0.16)
            if row_index == 1:
                ax.set_xlabel("Estimate position (0 = first, 1 = last)")
            if column_index == 0:
                ax.set_ylabel("Normalized estimate: (estimate − tau) / tau")
            if task_curves:
                ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Reasoning trajectories by format and condition")
    fig.tight_layout()
    _save_figure(fig, output_dir / "reasoning_trajectories")
    plot_data_dir = output_dir / "plot_data"
    plot_data_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(plot_data_dir / "trajectory_rollouts.npz", **npz_payload)
    write_json(plot_data_dir / "trajectory_rollout_ids.json", mapping)
    _write_csv(plot_data_dir / "trajectory_summary.csv", summary_rows)


def generate_plots(
    study: str,
    judged_path: Path,
    thresholds_path: Path,
    metrics_path: Path,
    tasks: dict[str, Any],
    output_dir: Path,
) -> None:
    judged = list(read_jsonl(judged_path))
    thresholds = json.loads(thresholds_path.read_text(encoding="utf-8"))
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_bias_by_question(metrics, output_dir)
    plot_overall(metrics, output_dir)
    plot_distributions(judged, thresholds, tasks, output_dir)
    plot_trajectories(judged, thresholds, study, output_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", choices=("pilot", "main"), required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    parser.add_argument("--tasks", type=Path, default=ROOT / "tasks.yaml")
    parser.add_argument("--judged", type=Path)
    parser.add_argument("--thresholds", type=Path)
    parser.add_argument("--metrics", type=Path)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    validate_tasks_file(config, args.tasks)
    tasks = load_tasks(args.tasks)
    base_dir = run_dir(config, args.study)
    output_dir = args.output_dir or base_dir / "figures"
    generate_plots(
        args.study,
        args.judged or base_dir / "judged.jsonl",
        args.thresholds or base_dir / "prepared" / "thresholds.json",
        args.metrics or base_dir / "metrics" / "metrics.json",
        tasks,
        output_dir,
    )
    print(f"Saved PNG/PDF figures and plot data to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
