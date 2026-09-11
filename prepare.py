#!/usr/bin/env python3
"""Freeze E1 baseline thresholds, bounds, and all six prompt previews."""

from __future__ import annotations

import argparse
import copy
from fractions import Fraction
from pathlib import Path
from typing import Any

import yaml

from e1lib import (
    CONDITIONS,
    FORMATS,
    ROOT,
    atomic_write_text,
    build_prompt,
    exact_median,
    fraction_record,
    load_config,
    load_tasks,
    read_jsonl,
    rounded_bounds,
    run_dir,
    sha256_text,
    study_tasks,
    validate_bounds,
    validate_tasks_file,
    verify_directional_prompt_pair,
    write_json,
)


def _valid_baseline_rows(
    rows: list[dict[str, Any]], study: str, task: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected = [
        row
        for row in rows
        if row.get("study") == study
        and row.get("task") == task
        and row.get("format") == "unrestricted"
        and row.get("condition") == "baseline"
    ]
    ids = [row.get("sample_id") for row in selected]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate unrestricted baseline sample IDs for {task}")
    valid: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for row in selected:
        estimate = row.get("final_estimate")
        if isinstance(estimate, int) and not isinstance(estimate, bool):
            valid.append(row)
        else:
            excluded.append(row)
    return valid, excluded


def prepare_study(
    config: dict[str, Any],
    tasks: dict[str, Any],
    study: str,
    judged_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    judged = list(read_jsonl(judged_path))
    configured_tasks = study_tasks(config, tasks, study)
    lower_multiplier = float(config["bounds"]["lower_multiplier"])
    upper_multiplier = float(config["bounds"]["upper_multiplier"])
    expected_baselines = int(config["studies"][study]["samples_per_cell"])
    thresholds: dict[str, Any] = {
        "study": study,
        "source_judged_file": str(judged_path.resolve()),
        "tasks": {},
        "errors": {},
    }
    prompts: dict[str, Any] = {"study": study, "prompts": {}}

    for task_name in configured_tasks:
        try:
            valid, excluded = _valid_baseline_rows(judged, study, task_name)
            if len(valid) + len(excluded) != expected_baselines:
                raise ValueError(
                    f"Expected exactly {expected_baselines} sampled unrestricted baselines before "
                    f"exclusions, found {len(valid) + len(excluded)}"
                )
            if not valid:
                raise ValueError("No valid unrestricted baseline final estimates")
            estimates = [int(row["final_estimate"]) for row in valid]
            threshold = exact_median(estimates)
            if threshold <= 0:
                raise ValueError(f"Median threshold must be positive, got {threshold}")
            lower, upper = rounded_bounds(threshold, lower_multiplier, upper_multiplier)
            validate_bounds(threshold, lower, upper)
            coverage_count = sum(lower <= estimate <= upper for estimate in estimates)
            threshold_data = {
                **fraction_record(threshold),
                "lower_bound": lower,
                "upper_bound": upper,
                "lower_multiplier": lower_multiplier,
                "upper_multiplier": upper_multiplier,
                "baseline_ids": [row["sample_id"] for row in valid],
                "excluded_baseline_ids": [row["sample_id"] for row in excluded],
                "baseline_sample_count": len(valid) + len(excluded),
                "valid_baseline_count": len(valid),
                "excluded_baseline_count": len(excluded),
                "unrestricted_baseline_in_bounds_count": coverage_count,
                "unrestricted_baseline_in_bounds_fraction": coverage_count / len(estimates),
            }
            thresholds["tasks"][task_name] = threshold_data

            task_prompts: dict[str, Any] = {}
            for fmt in FORMATS:
                task_prompts[fmt] = {}
                for condition in CONDITIONS:
                    prompt = build_prompt(
                        question=tasks[task_name]["question"],
                        fmt=fmt,
                        condition=condition,
                        threshold=threshold if condition != "baseline" else None,
                        lower_bound=lower if fmt == "bounded" else None,
                        upper_bound=upper if fmt == "bounded" else None,
                    )
                    metadata_threshold = threshold_data["threshold"] if (
                        condition != "baseline" or fmt == "bounded"
                    ) else None
                    task_prompts[fmt][condition] = {
                        "prompt_id": f"{study}:{task_name}:{fmt}:{condition}",
                        "task": task_name,
                        "format": fmt,
                        "condition": condition,
                        "threshold": metadata_threshold,
                        "threshold_exact": threshold_data["threshold_exact"] if metadata_threshold is not None else None,
                        "threshold_numerator": threshold.numerator if metadata_threshold is not None else None,
                        "threshold_denominator": threshold.denominator if metadata_threshold is not None else None,
                        "lower_bound": lower if fmt == "bounded" else None,
                        "upper_bound": upper if fmt == "bounded" else None,
                        "prompt": prompt,
                        "prompt_sha256": sha256_text(prompt),
                    }
                verify_directional_prompt_pair(
                    task_prompts[fmt]["above_good"]["prompt"],
                    task_prompts[fmt]["below_good"]["prompt"],
                    fmt,
                    threshold,
                )
            prompts["prompts"][task_name] = task_prompts
        except ValueError as exc:
            thresholds["errors"][task_name] = str(exc)

    return thresholds, prompts


def _frozen_projection(data: dict[str, Any]) -> dict[str, Any]:
    projection = copy.deepcopy(data)
    projection.pop("source_judged_file", None)
    return projection


def save_prepared(
    output_dir: Path,
    thresholds: dict[str, Any],
    prompts: dict[str, Any],
    config: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    thresholds_path = output_dir / "thresholds.json"
    prompts_path = output_dir / "prompts.json"
    if thresholds_path.exists():
        import json

        existing = json.loads(thresholds_path.read_text(encoding="utf-8"))
        if _frozen_projection(existing) != _frozen_projection(thresholds):
            raise ValueError(
                f"Refusing to overwrite changed frozen thresholds at {thresholds_path}. "
                "Use a new study directory."
            )
    if prompts_path.exists():
        import json

        existing_prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
        if existing_prompts != prompts:
            raise ValueError(
                f"Refusing to overwrite changed frozen prompts at {prompts_path}. "
                "Use a new study directory."
            )
    write_json(thresholds_path, thresholds)
    write_json(prompts_path, prompts)
    atomic_write_text(
        output_dir / "config.snapshot.yaml",
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", choices=("pilot", "main"), required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    parser.add_argument("--tasks", type=Path, default=ROOT / "tasks.yaml")
    parser.add_argument("--judged", type=Path)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    validate_tasks_file(config, args.tasks)
    tasks = load_tasks(args.tasks)
    base_dir = run_dir(config, args.study)
    judged_path = args.judged or base_dir / "judged.jsonl"
    output_dir = args.output_dir or base_dir / "prepared"
    thresholds, prompts = prepare_study(config, tasks, args.study, judged_path)
    save_prepared(output_dir, thresholds, prompts, config)
    print(f"Prepared {len(thresholds['tasks'])} task(s) in {output_dir}")
    if thresholds["errors"]:
        for task, error in thresholds["errors"].items():
            print(f"ERROR {task}: {error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
