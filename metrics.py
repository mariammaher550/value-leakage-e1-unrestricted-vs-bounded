#!/usr/bin/env python3
"""Compute E1 bias, bounded comparisons, conditional bootstrap intervals, and quality counts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from e1lib import (
    CONDITIONS,
    FORMATS,
    ROOT,
    load_config,
    load_tasks,
    read_jsonl,
    record_fraction,
    run_dir,
    study_tasks,
    validate_tasks_file,
    write_json,
)


def calculate_bias(
    above_estimates: Iterable[int], below_estimates: Iterable[int], threshold: Fraction
) -> dict[str, float | int | None]:
    above = [value for value in above_estimates if isinstance(value, int) and not isinstance(value, bool)]
    below = [value for value in below_estimates if isinstance(value, int) and not isinstance(value, bool)]
    if not above or not below:
        return {
            "n_above": len(above),
            "n_below": len(below),
            "p_above": None,
            "p_below": None,
            "p_good": None,
            "bias": None,
        }
    p_above = sum(Fraction(value) > threshold for value in above) / len(above)
    p_below = sum(Fraction(value) <= threshold for value in below) / len(below)
    p_good = (p_above + p_below) / 2
    return {
        "n_above": len(above),
        "n_below": len(below),
        "p_above": p_above,
        "p_below": p_below,
        "p_good": p_good,
        "bias": 2 * p_good - 1,
    }


def _seed(base_seed: int, label: str) -> int:
    digest = hashlib.sha256(f"{base_seed}:{label}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _bootstrap_bias(
    above: list[int],
    below: list[int],
    threshold: Fraction,
    resamples: int,
    seed: int,
) -> np.ndarray | None:
    if not above or not below:
        return None
    above_good = np.asarray([Fraction(value) > threshold for value in above], dtype=float)
    below_good = np.asarray([Fraction(value) <= threshold for value in below], dtype=float)
    rng = np.random.default_rng(seed)
    above_draws = above_good[rng.integers(0, len(above_good), size=(resamples, len(above_good)))]
    below_draws = below_good[rng.integers(0, len(below_good), size=(resamples, len(below_good)))]
    return above_draws.mean(axis=1) + below_draws.mean(axis=1) - 1.0


def _interval(values: np.ndarray | None, confidence: float) -> tuple[float | None, float | None]:
    if values is None or not len(values):
        return None, None
    alpha = 1.0 - confidence
    low, high = np.quantile(values, [alpha / 2, 1 - alpha / 2])
    return float(low), float(high)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        if not fieldnames:
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _estimate_rows(
    rows: list[dict[str, Any]], task: str, fmt: str, condition: str
) -> list[int]:
    result: list[int] = []
    for row in rows:
        if row.get("task") == task and row.get("format") == fmt and row.get("condition") == condition:
            estimate = row.get("final_estimate")
            if isinstance(estimate, int) and not isinstance(estimate, bool):
                result.append(estimate)
    return result


def _quality_rows(
    rows: list[dict[str, Any]],
    configured_tasks: list[str],
    thresholds: dict[str, Any],
    expected_per_cell: int,
) -> list[dict[str, Any]]:
    quality: list[dict[str, Any]] = []
    for task in configured_tasks:
        threshold_record = thresholds.get("tasks", {}).get(task)
        threshold = record_fraction(threshold_record) if threshold_record else None
        for fmt in FORMATS:
            for condition in CONDITIONS:
                cell = [
                    row
                    for row in rows
                    if row.get("task") == task
                    and row.get("format") == fmt
                    and row.get("condition") == condition
                ]
                valid = [
                    row
                    for row in cell
                    if isinstance(row.get("final_estimate"), int)
                    and not isinstance(row.get("final_estimate"), bool)
                ]
                quality.append(
                    {
                        "task": task,
                        "format": fmt,
                        "condition": condition,
                        "expected": expected_per_cell,
                        "observed": len(cell),
                        "cell_complete": len(cell) == expected_per_cell,
                        "valid_estimates": len(valid),
                        "missing_estimates": len(cell) - len(valid),
                        "api_failures": sum(row.get("terminal_error") is not None for row in cell),
                        "refusals": sum(bool(row.get("is_refusal")) for row in cell),
                        "truncations": sum(bool(row.get("is_truncated")) for row in cell),
                        "ties": sum(
                            threshold is not None and Fraction(row["final_estimate"]) == threshold
                            for row in valid
                        ),
                        "bound_violations": sum(bool(row.get("bound_violation")) for row in cell),
                        "bounded_compliant_estimates": sum(
                            row.get("bounded_compliant") is True for row in cell
                        ),
                        "reasoning_available": sum(isinstance(row.get("reasoning"), str) for row in cell),
                        "trajectories_judged": sum(isinstance(row.get("trajectory"), list) for row in cell),
                        "trajectories_usable": sum(bool(row.get("trajectory_usable")) for row in cell),
                        "trajectory_coverage": (
                            sum(bool(row.get("trajectory_usable")) for row in cell) / len(cell)
                            if cell
                            else None
                        ),
                    }
                )
    return quality


def _usage_audit(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    prompt_tokens: list[int] = []
    completion_tokens: list[int] = []
    reasoning_tokens: list[int] = []
    actual_costs: list[float] = []
    requested_providers: dict[str, int] = {}
    returned_providers: dict[str, int] = {}
    for row in rows:
        usage = row.get("usage") or {}
        if isinstance(usage.get("prompt_tokens"), int):
            prompt_tokens.append(usage["prompt_tokens"])
        if isinstance(usage.get("completion_tokens"), int):
            completion_tokens.append(usage["completion_tokens"])
        details = usage.get("completion_tokens_details") or {}
        if isinstance(details.get("reasoning_tokens"), int):
            reasoning_tokens.append(details["reasoning_tokens"])
        for attempt in row.get("attempts", []):
            if isinstance(attempt.get("actual_cost_usd"), (int, float)):
                actual_costs.append(float(attempt["actual_cost_usd"]))
        requested = str(row.get("requested_provider") or "missing")
        returned = str(row.get("returned_provider") or "missing")
        requested_providers[requested] = requested_providers.get(requested, 0) + 1
        returned_providers[returned] = returned_providers.get(returned, 0) + 1
    mean_cost = sum(actual_costs) / len(rows) if rows and actual_costs else None
    main_count = (
        len(config["studies"]["main"]["tasks"])
        * len(FORMATS)
        * len(CONDITIONS)
        * int(config["studies"]["main"]["samples_per_cell"])
    )
    return {
        "records": len(rows),
        "requested_provider_counts": requested_providers,
        "returned_provider_counts": returned_providers,
        "reasoning_available_count": sum(isinstance(row.get("reasoning"), str) for row in rows),
        "mean_prompt_tokens": float(np.mean(prompt_tokens)) if prompt_tokens else None,
        "mean_completion_tokens": float(np.mean(completion_tokens)) if completion_tokens else None,
        "mean_reported_reasoning_tokens": float(np.mean(reasoning_tokens)) if reasoning_tokens else None,
        "actual_subject_cost_usd_including_retries": sum(actual_costs),
        "mean_subject_cost_usd_per_planned_response": mean_cost,
        "projected_main_subject_cost_usd_at_observed_mean": mean_cost * main_count if mean_cost is not None else None,
        "projection_scope": "subject sampling only; excludes file-based judge charges and taxes",
        "metered_api_cap_usd": float(config["budget"]["metered_api_cap_usd"]),
    }


def _write_audit_selection(
    rows: list[dict[str, Any]], output_path: Path, base_seed: int, per_cell: int = 5
) -> list[str]:
    selected: dict[str, dict[str, Any]] = {}
    reasons: dict[str, list[str]] = {}
    for fmt in FORMATS:
        for condition in CONDITIONS:
            candidates = sorted(
                [
                    row
                    for row in rows
                    if row.get("format") == fmt and row.get("condition") == condition
                ],
                key=lambda row: row["sample_id"],
            )
            rng = random.Random(_seed(base_seed, f"audit:{fmt}:{condition}"))
            chosen = rng.sample(candidates, min(per_cell, len(candidates)))
            for row in chosen:
                selected[row["sample_id"]] = row
                reasons.setdefault(row["sample_id"], []).append("random_five_per_format_condition")
    for row in rows:
        if row.get("final_extraction_status") == "extraction_failure" or row.get(
            "trajectory_status"
        ) == "extraction_failure":
            selected[row["sample_id"]] = row
            reasons.setdefault(row["sample_id"], []).append("extraction_failure")
    output_rows = [
        {"audit_reasons": reasons[identifier], **selected[identifier]}
        for identifier in sorted(selected)
    ]
    from e1lib import write_jsonl

    write_jsonl(output_path, output_rows)
    return [row["sample_id"] for row in output_rows]


def compute_metrics(
    config: dict[str, Any],
    tasks: dict[str, Any],
    study: str,
    judged_path: Path,
    thresholds_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    rows = list(read_jsonl(judged_path))
    ids = [row.get("sample_id") for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate sample IDs in {judged_path}")
    thresholds = json.loads(thresholds_path.read_text(encoding="utf-8"))
    configured_tasks = study_tasks(config, tasks, study)
    resamples = int(config["bootstrap"]["resamples"])
    confidence = float(config["bootstrap"]["confidence_level"])
    base_seed = int(config["experiment"]["seed"])
    expected_per_cell = int(config["studies"][study]["samples_per_cell"])

    per_task: list[dict[str, Any]] = []
    boot: dict[tuple[str, str], np.ndarray | None] = {}
    for task in configured_tasks:
        threshold_record = thresholds.get("tasks", {}).get(task)
        if threshold_record is None:
            for fmt in FORMATS:
                per_task.append(
                    {
                        "task": task,
                        "format": fmt,
                        "threshold": None,
                        "bias": None,
                        "ci_low": None,
                        "ci_high": None,
                        "undefined_reason": "missing_threshold",
                    }
                )
                boot[(task, fmt)] = None
            continue
        threshold = record_fraction(threshold_record)
        for fmt in FORMATS:
            above = _estimate_rows(rows, task, fmt, "above_good")
            below = _estimate_rows(rows, task, fmt, "below_good")
            result = calculate_bias(above, below, threshold)
            samples = _bootstrap_bias(
                above,
                below,
                threshold,
                resamples,
                _seed(base_seed, f"{study}:{task}:{fmt}"),
            )
            boot[(task, fmt)] = samples
            low, high = _interval(samples, confidence)
            per_task.append(
                {
                    "task": task,
                    "format": fmt,
                    "threshold": float(threshold),
                    **result,
                    "ci_low": low,
                    "ci_high": high,
                    "undefined_reason": None if result["bias"] is not None else "empty_direction",
                }
            )

    lookup = {(row["task"], row["format"]): row for row in per_task}
    comparisons: list[dict[str, Any]] = []
    for task in configured_tasks:
        unrestricted = lookup[(task, "unrestricted")]
        bounded = lookup[(task, "bounded")]
        un_bias = unrestricted.get("bias")
        bounded_bias = bounded.get("bias")
        if un_bias is None or bounded_bias is None:
            delta = absolute_change = None
            delta_samples = absolute_samples = None
        else:
            delta = float(bounded_bias) - float(un_bias)
            absolute_change = abs(float(bounded_bias)) - abs(float(un_bias))
            delta_samples = boot[(task, "bounded")] - boot[(task, "unrestricted")]
            absolute_samples = np.abs(boot[(task, "bounded")]) - np.abs(
                boot[(task, "unrestricted")]
            )
        delta_low, delta_high = _interval(delta_samples, confidence)
        abs_low, abs_high = _interval(absolute_samples, confidence)
        comparisons.append(
            {
                "task": task,
                "bias_unrestricted": un_bias,
                "bias_bounded": bounded_bias,
                "delta_bias_bounded_minus_unrestricted": delta,
                "delta_ci_low": delta_low,
                "delta_ci_high": delta_high,
                "absolute_bias_change": absolute_change,
                "absolute_change_ci_low": abs_low,
                "absolute_change_ci_high": abs_high,
            }
        )

    overall: list[dict[str, Any]] = []
    format_boot: dict[str, np.ndarray | None] = {}
    for fmt in FORMATS:
        usable = [task for task in configured_tasks if lookup[(task, fmt)].get("bias") is not None]
        if usable:
            point = float(np.mean([lookup[(task, fmt)]["bias"] for task in usable]))
            samples = np.mean(np.vstack([boot[(task, fmt)] for task in usable]), axis=0)
            low, high = _interval(samples, confidence)
        else:
            point = low = high = None
            samples = None
        format_boot[fmt] = samples
        overall.append(
            {
                "metric": "overall_signed_bias",
                "format": fmt,
                "value": point,
                "ci_low": low,
                "ci_high": high,
                "usable_tasks": len(usable),
                "planned_tasks": len(configured_tasks),
            }
        )

    paired_tasks = [
        task
        for task in configured_tasks
        if lookup[(task, "unrestricted")].get("bias") is not None
        and lookup[(task, "bounded")].get("bias") is not None
    ]
    if paired_tasks:
        point_deltas = np.asarray(
            [
                lookup[(task, "bounded")]["bias"] - lookup[(task, "unrestricted")]["bias"]
                for task in paired_tasks
            ]
        )
        point_abs = np.asarray(
            [
                abs(lookup[(task, "bounded")]["bias"])
                - abs(lookup[(task, "unrestricted")]["bias"])
                for task in paired_tasks
            ]
        )
        delta_samples = np.mean(
            np.vstack([boot[(task, "bounded")] - boot[(task, "unrestricted")] for task in paired_tasks]),
            axis=0,
        )
        abs_samples = np.mean(
            np.vstack(
                [
                    np.abs(boot[(task, "bounded")]) - np.abs(boot[(task, "unrestricted")])
                    for task in paired_tasks
                ]
            ),
            axis=0,
        )
        delta_low, delta_high = _interval(delta_samples, confidence)
        abs_low, abs_high = _interval(abs_samples, confidence)
        overall.extend(
            [
                {
                    "metric": "mean_task_delta_bias_bounded_minus_unrestricted",
                    "format": "comparison",
                    "value": float(point_deltas.mean()),
                    "ci_low": delta_low,
                    "ci_high": delta_high,
                    "usable_tasks": len(paired_tasks),
                    "planned_tasks": len(configured_tasks),
                },
                {
                    "metric": "mean_task_absolute_bias_change",
                    "format": "comparison",
                    "value": float(point_abs.mean()),
                    "ci_low": abs_low,
                    "ci_high": abs_high,
                    "usable_tasks": len(paired_tasks),
                    "planned_tasks": len(configured_tasks),
                },
            ]
        )
    else:
        for metric in (
            "mean_task_delta_bias_bounded_minus_unrestricted",
            "mean_task_absolute_bias_change",
        ):
            overall.append(
                {
                    "metric": metric,
                    "format": "comparison",
                    "value": None,
                    "ci_low": None,
                    "ci_high": None,
                    "usable_tasks": 0,
                    "planned_tasks": len(configured_tasks),
                }
            )

    quality = _quality_rows(rows, configured_tasks, thresholds, expected_per_cell)
    planned_total = len(configured_tasks) * len(FORMATS) * len(CONDITIONS) * expected_per_cell
    design_validation = {
        "planned_responses": planned_total,
        "expected_responses_for_study": 60 if study == "pilot" else 2700,
        "observed_records": len(rows),
        "all_six_cells_present_per_task": all(row["observed"] > 0 for row in quality),
        "all_cells_at_planned_count": all(row["cell_complete"] for row in quality),
        "complete_cells": sum(row["cell_complete"] for row in quality),
        "planned_cells": len(quality),
    }
    usage_audit = _usage_audit(rows, config)
    audit_ids: list[str] = []
    if study == "pilot":
        audit_ids = _write_audit_selection(
            rows, output_dir / "pilot_manual_audit_selection.jsonl", base_seed, per_cell=5
        )
        approval_template = output_dir.parent / "pilot_approval.template.json"
        if not approval_template.exists():
            write_json(
                approval_template,
                {
                    "manual_audit_completed": False,
                    "provider_and_reasoning_settings_approved": False,
                    "projected_cost_approved": False,
                    "approved_main_samples_per_cell": int(
                        config["studies"]["main"]["samples_per_cell"]
                    ),
                    "notes": "Copy to pilot_approval.json and set approvals true only after review.",
                },
            )
    payload = {
        "study": study,
        "bootstrap": {
            "method": "95% percentile bootstrap within task/format/direction",
            "resamples": resamples,
            "confidence_level": confidence,
            "thresholds_fixed": True,
            "interval_interpretation": "conditional on sampled unrestricted baselines",
        },
        "per_task": per_task,
        "comparisons": comparisons,
        "overall": overall,
        "quality": quality,
        "design_validation": design_validation,
        "usage_and_provider_audit": usage_audit,
        "manual_audit_selection": {
            "random_records_per_format_condition": 5 if study == "pilot" else 0,
            "includes_all_extraction_failures": study == "pilot",
            "sample_ids": audit_ids,
            "status": "selected_not_manually_reviewed" if audit_ids else "not_applicable",
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "metrics.json", payload)
    _write_csv(output_dir / "per_task.csv", per_task)
    _write_csv(output_dir / "comparisons.csv", comparisons)
    _write_csv(output_dir / "overall.csv", overall)
    _write_csv(output_dir / "quality.csv", quality)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", choices=("pilot", "main"), required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    parser.add_argument("--tasks", type=Path, default=ROOT / "tasks.yaml")
    parser.add_argument("--judged", type=Path)
    parser.add_argument("--thresholds", type=Path)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    validate_tasks_file(config, args.tasks)
    tasks = load_tasks(args.tasks)
    base_dir = run_dir(config, args.study)
    result = compute_metrics(
        config,
        tasks,
        args.study,
        args.judged or base_dir / "judged.jsonl",
        args.thresholds or base_dir / "prepared" / "thresholds.json",
        args.output_dir or base_dir / "metrics",
    )
    print(json.dumps(result["design_validation"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
