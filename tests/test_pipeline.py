from __future__ import annotations

import asyncio
import copy
import json
from fractions import Fraction
from pathlib import Path

import httpx
import pytest

from e1lib import (
    build_prompt,
    load_config,
    load_tasks,
    read_jsonl,
    rounded_bounds,
    sample_id,
    write_json,
    write_jsonl,
)
from judge import FINAL_INSTRUCTIONS, TRAJECTORY_INSTRUCTIONS, export_batches, import_results
from metrics import calculate_bias, compute_metrics
from plots import generate_plots
from prepare import prepare_study, save_prepared
from sample import collect, validate_main_gate


ROOT = Path(__file__).resolve().parents[1]


def _pilot_config() -> dict:
    config = load_config(ROOT / "config.yaml")
    config = copy.deepcopy(config)
    config["bootstrap"]["resamples"] = 100
    config["model"]["max_retries"] = 0
    config["model"]["max_completion_tokens"] = 100
    config["budget"]["metered_api_cap_usd"] = 10
    return config


def _raw_row(index: int, fmt: str, condition: str, estimate: int, *, study: str = "pilot") -> dict:
    identifier = sample_id(study, "giraffes", fmt, condition, index)
    prompt = build_prompt(
        load_tasks(ROOT / "tasks.yaml")["giraffes"]["question"],
        fmt,
        condition,
        threshold=Fraction(55) if condition != "baseline" else None,
        lower_bound=27 if fmt == "bounded" else None,
        upper_bound=83 if fmt == "bounded" else None,
    )
    return {
        "sample_id": identifier,
        "sample_index": index,
        "study": study,
        "task": "giraffes",
        "format": fmt,
        "condition": condition,
        "prompt": prompt,
        "prompt_sha256": "test",
        "threshold": 55 if (fmt == "bounded" or condition != "baseline") else None,
        "lower_bound": 27 if fmt == "bounded" else None,
        "upper_bound": 83 if fmt == "bounded" else None,
        "final_answer": f"My final estimate is {estimate}.",
        "reasoning": f"I first considered {estimate - 1}, then settled on {estimate}.",
        "refusal": None,
        "finish_reason": "stop",
        "terminal_error": None,
        "attempts": [],
    }


def _judged_row(index: int, fmt: str, condition: str, estimate: int, *, study: str = "pilot") -> dict:
    row = _raw_row(index, fmt, condition, estimate, study=study)
    row.update(
        {
            "final_estimate": estimate,
            "final_extraction_status": "ok",
            "trajectory": [estimate - 1, estimate],
            "trajectory_status": "ok",
            "trajectory_usable": True,
            "bound_violation": fmt == "bounded" and not (27 <= estimate <= 83),
            "bounded_compliant": None if fmt == "unrestricted" else 27 <= estimate <= 83,
            "is_refusal": False,
            "is_truncated": False,
        }
    )
    return row


def test_bias_sanity_checks_and_tie_rule() -> None:
    tau = Fraction(10)
    neutral = calculate_bias([9, 11], [9, 11], tau)
    favored = calculate_bias([11, 12], [9, 10], tau)
    reversed_result = calculate_bias([9, 10], [11, 12], tau)
    assert neutral["bias"] == 0
    assert favored["bias"] == 1
    assert reversed_result["bias"] == -1
    assert calculate_bias([11, 11, 9], [10], tau)["bias"] == pytest.approx(2 / 3)


def test_bounds_and_prompt_pair() -> None:
    assert rounded_bounds(Fraction(55), 0.5, 1.5) == (27, 83)
    tasks = load_tasks(ROOT / "tasks.yaml")
    bounded = build_prompt(tasks["giraffes"]["question"], "bounded", "baseline", lower_bound=27, upper_bound=83)
    assert "between 27 and 83, inclusive" in bounded
    assert "threshold" not in bounded.lower()
    assert "bet with a friend" not in bounded


def test_prepare_uses_only_fresh_unrestricted_baseline(tmp_path: Path) -> None:
    config = _pilot_config()
    tasks = load_tasks(ROOT / "tasks.yaml")
    rows = [_judged_row(i, "unrestricted", "baseline", (i + 1) * 10) for i in range(10)]
    rows.append(_judged_row(0, "bounded", "baseline", 9999))
    rows.append(_judged_row(0, "unrestricted", "above_good", 9999))
    rows.append(_judged_row(0, "unrestricted", "baseline", 1, study="main"))
    judged_path = tmp_path / "judged.jsonl"
    write_jsonl(judged_path, rows)
    thresholds, prompts = prepare_study(config, tasks, "pilot", judged_path)
    assert thresholds["tasks"]["giraffes"]["threshold"] == 55
    assert thresholds["tasks"]["giraffes"]["baseline_sample_count"] == 10
    assert len(prompts["prompts"]["giraffes"]) == 2
    output = tmp_path / "prepared"
    save_prepared(output, thresholds, prompts, config)
    save_prepared(output, thresholds, prompts, config)


def test_judge_export_anonymizes_and_import_preserves_return(tmp_path: Path) -> None:
    tasks = load_tasks(ROOT / "tasks.yaml")
    raw = [
        _raw_row(0, "bounded", "above_good", 90),
        _raw_row(1, "bounded", "above_good", 60),
    ]
    raw[1]["finish_reason"] = "length"
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, raw)
    export_dir = tmp_path / "exports"
    summary = export_batches(raw_path, tasks, export_dir, batch_size=1)
    assert summary["kinds"]["final"]["exported"] == 2
    assert summary["kinds"]["trajectory"]["exported"] == 1
    exported = list(read_jsonl(export_dir / "final" / "batch_0000" / "input.jsonl"))[0]
    assert "above_good" not in json.dumps(exported)
    assert "bounded" not in json.dumps(exported)
    assert "mere restatements" in TRAJECTORY_INSTRUCTIONS
    assert "duration_days" in FINAL_INSTRUCTIONS

    all_inputs = []
    for path in sorted((export_dir / "final").glob("batch_*/input.jsonl")):
        all_inputs.extend(read_jsonl(path))
    returned = tmp_path / "returned.jsonl"
    write_jsonl(
        returned,
        [
            {"id": all_inputs[0]["id"], "final_estimate": 90},
            {"id": all_inputs[1]["id"], "final_estimate": 60},
        ],
    )
    original_bytes = returned.read_bytes()
    report = import_results(
        kind="final",
        returned_paths=[returned],
        export_dir=export_dir,
        raw_path=raw_path,
        result_dir=tmp_path / "results",
        judged_path=tmp_path / "judged.jsonl",
        judge_app="Codex",
        judge_model="test-model",
    )
    assert report["ok"]
    saved_path = Path(report["saved_returned_files"][0]["saved"])
    assert saved_path.read_bytes() == original_bytes
    judged = list(read_jsonl(tmp_path / "judged.jsonl"))
    assert judged[0]["bound_violation"] is True
    assert judged[1]["is_truncated"] is True


def test_resume_skips_completed_sample(tmp_path: Path) -> None:
    config = _pilot_config()
    tasks = load_tasks(ROOT / "tasks.yaml")
    raw_path = tmp_path / "raw.jsonl"
    write_jsonl(raw_path, [_raw_row(0, "unrestricted", "baseline", 10)])
    calls = 0

    async def fake_request(client, body, headers):
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "id": "response-1",
                "model": config["model"]["id"],
                "provider": "darkbloom",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": "20", "reasoning": "First 10, then 20."},
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "cost": 0.001},
            },
        )

    result = asyncio.run(
        collect(
            config=config,
            tasks=tasks,
            study="pilot",
            task="giraffes",
            fmt="unrestricted",
            condition="baseline",
            count=2,
            raw_path=raw_path,
            ledger_path=tmp_path / "ledger.jsonl",
            prepared_path=tmp_path / "missing.json",
            api_key="test",
            concurrency=1,
            request_func=fake_request,
        )
    )
    assert calls == 1
    assert result["skipped"] == 1
    assert len(list(read_jsonl(raw_path))) == 2


def test_transient_retry_and_malformed_success_is_not_replaced(tmp_path: Path) -> None:
    config = _pilot_config()
    config["model"]["max_retries"] = 1
    config["model"]["retry_base_seconds"] = 0
    tasks = load_tasks(ROOT / "tasks.yaml")
    calls = 0

    async def retry_once(client, body, headers):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, text="temporary overload")
        return httpx.Response(
            200,
            json={
                "id": "response-2",
                "model": config["model"]["id"],
                "choices": [{"finish_reason": "stop", "message": {"content": "20"}}],
                "usage": {"cost": 0.001},
            },
        )

    raw_path = tmp_path / "retry_raw.jsonl"
    asyncio.run(
        collect(
            config=config,
            tasks=tasks,
            study="pilot",
            task="giraffes",
            fmt="unrestricted",
            condition="baseline",
            count=1,
            raw_path=raw_path,
            ledger_path=tmp_path / "retry_ledger.jsonl",
            prepared_path=tmp_path / "missing.json",
            api_key="test",
            concurrency=1,
            request_func=retry_once,
        )
    )
    row = list(read_jsonl(raw_path))[0]
    assert calls == 2
    assert len(row["attempts"]) == 2

    malformed_calls = 0

    async def malformed(client, body, headers):
        nonlocal malformed_calls
        malformed_calls += 1
        return httpx.Response(200, json={"choices": []})

    malformed_path = tmp_path / "malformed_raw.jsonl"
    asyncio.run(
        collect(
            config=config,
            tasks=tasks,
            study="pilot",
            task="giraffes",
            fmt="unrestricted",
            condition="baseline",
            count=1,
            raw_path=malformed_path,
            ledger_path=tmp_path / "malformed_ledger.jsonl",
            prepared_path=tmp_path / "missing.json",
            api_key="test",
            concurrency=1,
            request_func=malformed,
        )
    )
    malformed_row = list(read_jsonl(malformed_path))[0]
    assert malformed_calls == 1
    assert malformed_row["terminal_error"].startswith("Malformed response")


def test_partial_response_protocol_error_is_retried_and_conservatively_charged(
    tmp_path: Path,
) -> None:
    config = _pilot_config()
    config["model"]["max_retries"] = 1
    config["model"]["retry_base_seconds"] = 0
    tasks = load_tasks(ROOT / "tasks.yaml")
    calls = 0

    async def partial_then_success(client, body, headers):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.RemoteProtocolError("incomplete chunked read")
        return httpx.Response(
            200,
            json={
                "id": "response-after-partial",
                "model": config["model"]["id"],
                "provider": "darkbloom",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": "20", "reasoning": "Estimate 20."},
                    }
                ],
                "usage": {"cost": 0.001},
            },
        )

    raw_path = tmp_path / "protocol_raw.jsonl"
    asyncio.run(
        collect(
            config=config,
            tasks=tasks,
            study="pilot",
            task="giraffes",
            fmt="unrestricted",
            condition="baseline",
            count=1,
            raw_path=raw_path,
            ledger_path=tmp_path / "protocol_ledger.jsonl",
            prepared_path=tmp_path / "missing.json",
            api_key="test",
            concurrency=1,
            request_func=partial_then_success,
        )
    )
    row = list(read_jsonl(raw_path))[0]
    assert calls == 2
    assert len(row["attempts"]) == 2
    assert row["attempts"][0]["cost_source"] == "conservative_unknown_request_cost"
    assert row["attempts"][0]["actual_cost_usd"] > 0


def test_main_sampling_is_gated_on_completed_approved_pilot(tmp_path: Path) -> None:
    config = _pilot_config()
    config["paths"]["runs_dir"] = str(tmp_path / "runs")
    with pytest.raises(ValueError, match="pilot metrics"):
        validate_main_gate(config)


def test_synthetic_pipeline_metrics_and_plots(tmp_path: Path) -> None:
    config = _pilot_config()
    tasks = load_tasks(ROOT / "tasks.yaml")
    # The unrestricted baseline 10..100 freezes tau at 55 and bounds at 27..83.
    estimates = {
        ("unrestricted", "baseline"): list(range(10, 110, 10)),
        ("unrestricted", "above_good"): [60] * 10,
        ("unrestricted", "below_good"): [50] * 10,
        ("bounded", "baseline"): [55] * 10,
        ("bounded", "above_good"): [50, 60] * 5,
        ("bounded", "below_good"): [50, 60] * 5,
    }
    judged = [
        _judged_row(index, fmt, condition, estimate)
        for (fmt, condition), values in estimates.items()
        for index, estimate in enumerate(values)
    ]
    judged_path = tmp_path / "judged.jsonl"
    write_jsonl(judged_path, judged)
    thresholds, prompts = prepare_study(config, tasks, "pilot", judged_path)
    prepared_dir = tmp_path / "prepared"
    save_prepared(prepared_dir, thresholds, prompts, config)
    metrics_dir = tmp_path / "metrics"
    result = compute_metrics(
        config,
        tasks,
        "pilot",
        judged_path,
        prepared_dir / "thresholds.json",
        metrics_dir,
    )
    assert result["design_validation"]["planned_responses"] == 60
    assert result["design_validation"]["all_cells_at_planned_count"] is True
    lookup = {(row["task"], row["format"]): row for row in result["per_task"]}
    assert lookup[("giraffes", "unrestricted")]["bias"] == 1
    assert lookup[("giraffes", "bounded")]["bias"] == 0
    figure_dir = tmp_path / "figures"
    generate_plots(
        "pilot",
        judged_path,
        prepared_dir / "thresholds.json",
        metrics_dir / "metrics.json",
        tasks,
        figure_dir,
    )
    expected = [
        "bias_by_question.png",
        "bias_by_question.pdf",
        "overall_bias_and_difference.png",
        "final_estimate_distributions_giraffes.png",
        "reasoning_trajectories.pdf",
        "plot_data/trajectory_rollouts.npz",
    ]
    for relative in expected:
        assert (figure_dir / relative).exists(), relative
