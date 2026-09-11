#!/usr/bin/env python3
"""Collect append-only Qwen responses from OpenRouter with safe resume and budget accounting."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import uuid
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from typing import Any, Awaitable, Callable

import httpx
from dotenv import load_dotenv

from e1lib import (
    CONDITIONS,
    FORMATS,
    ROOT,
    append_jsonl,
    build_prompt,
    load_config,
    load_tasks,
    load_yaml,
    read_jsonl,
    run_dir,
    sample_id,
    sha256_text,
    study_tasks,
    validate_tasks_file,
)


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TRANSIENT_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}
RequestFunction = Callable[[httpx.AsyncClient, dict[str, Any], dict[str, str]], Awaitable[httpx.Response]]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _load_completed(raw_path: Path) -> dict[str, dict[str, Any]]:
    completed: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(raw_path):
        identifier = row.get("sample_id")
        if not isinstance(identifier, str):
            raise ValueError(f"Record without a string sample_id in {raw_path}")
        if identifier in completed:
            raise ValueError(f"Duplicate completed sample ID {identifier} in {raw_path}")
        completed[identifier] = row
    return completed


def _ledger_state(ledger_path: Path) -> tuple[float, dict[str, float]]:
    outstanding: dict[str, float] = {}
    actual_total = 0.0
    for event in read_jsonl(ledger_path):
        reservation_id = event.get("reservation_id")
        if not isinstance(reservation_id, str):
            raise ValueError(f"Malformed budget event in {ledger_path}")
        if event.get("event") == "reserve":
            if reservation_id in outstanding:
                raise ValueError(f"Duplicate budget reservation {reservation_id}")
            outstanding[reservation_id] = float(event["reserved_usd"])
        elif event.get("event") == "settle":
            if reservation_id not in outstanding:
                raise ValueError(f"Invalid budget settlement {reservation_id}")
            outstanding.pop(reservation_id)
            actual_total += float(event["actual_usd"])
        else:
            raise ValueError(f"Unknown budget event {event.get('event')!r}")
    return actual_total, outstanding


def _reservation_amount(config: dict[str, Any]) -> float:
    budget = config["budget"]
    model = config["model"]
    input_cost = (
        float(budget["reserved_input_tokens_per_request"])
        * float(budget["max_input_usd_per_million"])
        / 1_000_000
    )
    output_cost = (
        int(model["max_completion_tokens"])
        * float(budget["max_output_usd_per_million"])
        / 1_000_000
    )
    return input_cost + output_cost


def _usage_cost(usage: dict[str, Any] | None, config: dict[str, Any]) -> tuple[float, str]:
    usage = usage or {}
    if isinstance(usage.get("cost"), (int, float)):
        return float(usage["cost"]), "openrouter_usage"
    input_tokens = int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
    output_tokens = int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)
    budget = config["budget"]
    cost = (
        input_tokens * float(budget["max_input_usd_per_million"])
        + output_tokens * float(budget["max_output_usd_per_million"])
    ) / 1_000_000
    return cost, "configured_token_rates"


def _prompt_record(
    config: dict[str, Any],
    tasks: dict[str, Any],
    study: str,
    task: str,
    fmt: str,
    condition: str,
    prepared_path: Path,
) -> dict[str, Any]:
    # The unrestricted baseline is the only cell that can be sampled before tau exists.
    if fmt == "unrestricted" and condition == "baseline" and not prepared_path.exists():
        prompt = build_prompt(tasks[task]["question"], fmt, condition)
        return {
            "prompt_id": f"{study}:{task}:{fmt}:{condition}",
            "task": task,
            "format": fmt,
            "condition": condition,
            "threshold": None,
            "threshold_exact": None,
            "threshold_numerator": None,
            "threshold_denominator": None,
            "lower_bound": None,
            "upper_bound": None,
            "prompt": prompt,
            "prompt_sha256": sha256_text(prompt),
        }
    if not prepared_path.exists():
        raise ValueError(
            f"{fmt}/{condition} requires frozen preparation at {prepared_path}. "
            "Judge the unrestricted baseline and run prepare.py first."
        )
    prepared = json.loads(prepared_path.read_text(encoding="utf-8"))
    try:
        record = prepared["prompts"][task][fmt][condition]
    except KeyError as exc:
        raise ValueError(f"Prepared prompt missing for {task}/{fmt}/{condition}") from exc
    if sha256_text(record["prompt"]) != record["prompt_sha256"]:
        raise ValueError(f"Prepared prompt hash mismatch for {task}/{fmt}/{condition}")
    return record


def _request_body(config: dict[str, Any], prompt: str) -> dict[str, Any]:
    model = config["model"]
    provider = model.get("provider")
    body: dict[str, Any] = {
        "model": model["id"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": float(model["temperature"]),
        # OpenRouter's Darkbloom endpoint currently advertises the legacy
        # max_tokens name. The configured allowance remains provider-agnostic.
        "max_tokens": int(model["max_completion_tokens"]),
        "reasoning": dict(model["reasoning"]),
    }
    if provider:
        body["provider"] = {
            "only": [provider],
            "allow_fallbacks": bool(model.get("allow_provider_fallbacks", False)),
            "require_parameters": True,
        }
    return body


def validate_main_gate(config: dict[str, Any]) -> dict[str, Any]:
    pilot_dir = run_dir(config, "pilot")
    metrics_path = pilot_dir / "metrics" / "metrics.json"
    approval_path = pilot_dir / "pilot_approval.json"
    snapshot_path = pilot_dir / "prepared" / "config.snapshot.yaml"
    if not metrics_path.exists():
        raise ValueError("Main study is blocked until pilot metrics have been generated")
    if not approval_path.exists():
        raise ValueError(
            f"Main study is blocked pending manual pilot approval. Review the pilot, then copy "
            f"{pilot_dir / 'pilot_approval.template.json'} to {approval_path} and complete it."
        )
    if not snapshot_path.exists():
        raise ValueError("Main study is blocked because the frozen pilot configuration is missing")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    design = metrics.get("design_validation", {})
    if not design.get("all_cells_at_planned_count") or design.get("observed_records") != 60:
        raise ValueError("Main study is blocked until all 60 planned pilot records are present")
    snapshot = load_yaml(snapshot_path)
    frozen_keys = ("experiment", "model", "bounds", "sources")
    changed_keys = [key for key in frozen_keys if snapshot.get(key) != config.get(key)]
    if changed_keys:
        raise ValueError(
            "Main experimental settings differ from the frozen pilot configuration: "
            f"{changed_keys}"
        )
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    required_approvals = (
        "manual_audit_completed",
        "provider_and_reasoning_settings_approved",
        "projected_cost_approved",
    )
    missing_approvals = [key for key in required_approvals if approval.get(key) is not True]
    if missing_approvals:
        raise ValueError(f"Main study is blocked by incomplete pilot approvals: {missing_approvals}")
    configured_count = int(config["studies"]["main"]["samples_per_cell"])
    if approval.get("approved_main_samples_per_cell") != configured_count:
        raise ValueError(
            "Approved main samples-per-cell does not match config.yaml; revise the count explicitly "
            "and re-approve it"
        )
    audit = metrics.get("usage_and_provider_audit", {})
    projected_main = audit.get("projected_main_subject_cost_usd_at_observed_mean")
    if not isinstance(projected_main, (int, float)):
        raise ValueError("Main study is blocked because pilot cost projection is unavailable")
    actual_pilot, outstanding_pilot = _ledger_state(pilot_dir / "budget_ledger.jsonl")
    commitment = actual_pilot + sum(outstanding_pilot.values()) + float(projected_main)
    cap = float(config["budget"]["metered_api_cap_usd"])
    if commitment > cap + 1e-12:
        raise ValueError(
            f"Main study projected subject commitment ${commitment:.2f} exceeds ${cap:.2f} API cap; "
            "revise samples_per_cell explicitly and re-approve"
        )
    return {
        "pilot_actual_usd": actual_pilot,
        "pilot_outstanding_reserved_usd": sum(outstanding_pilot.values()),
        "projected_main_subject_usd": float(projected_main),
        "projected_total_subject_commitment_usd": commitment,
        "metered_api_cap_usd": cap,
        "approved_main_samples_per_cell": configured_count,
    }


async def _default_request(
    client: httpx.AsyncClient, body: dict[str, Any], headers: dict[str, str]
) -> httpx.Response:
    return await client.post(OPENROUTER_URL, headers=headers, json=body)


def _response_provider(payload: dict[str, Any]) -> str | None:
    metadata = payload.get("openrouter_metadata")
    if isinstance(metadata, dict):
        endpoints = metadata.get("endpoints")
        if isinstance(endpoints, dict) and isinstance(endpoints.get("available"), list):
            for endpoint in endpoints["available"]:
                if isinstance(endpoint, dict) and endpoint.get("selected") and endpoint.get("provider"):
                    return str(endpoint["provider"])
        for key in ("provider_name", "provider", "slug"):
            if metadata.get(key):
                return str(metadata[key])
    if payload.get("provider"):
        return str(payload["provider"])
    return None


def _extract_response(payload: dict[str, Any]) -> dict[str, Any]:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("OpenRouter response has no choices")
    choice = choices[0]
    message = choice.get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        content = "".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
    reasoning = message.get("reasoning")
    if reasoning is None:
        reasoning = message.get("reasoning_content")
    return {
        "final_answer": content if isinstance(content, str) else "",
        "reasoning": reasoning if isinstance(reasoning, str) else None,
        "refusal": message.get("refusal"),
        "finish_reason": choice.get("finish_reason"),
        "usage": payload.get("usage") if isinstance(payload.get("usage"), dict) else None,
        "response_id": payload.get("id"),
        "returned_model": payload.get("model"),
        "returned_provider": _response_provider(payload),
        "openrouter_metadata": payload.get("openrouter_metadata"),
    }


async def collect(
    *,
    config: dict[str, Any],
    tasks: dict[str, Any],
    study: str,
    task: str,
    fmt: str,
    condition: str,
    count: int,
    raw_path: Path,
    ledger_path: Path,
    prepared_path: Path,
    api_key: str,
    concurrency: int,
    request_func: RequestFunction = _default_request,
    assume_pending_unbilled: bool = False,
    assume_pending_billed: bool = False,
) -> dict[str, Any]:
    if task not in study_tasks(config, tasks, study):
        raise ValueError(f"Task {task!r} is not configured for study {study!r}")
    prompt_record = _prompt_record(config, tasks, study, task, fmt, condition, prepared_path)
    body = _request_body(config, prompt_record["prompt"])
    settings = {key: value for key, value in body.items() if key != "messages"}
    completed = _load_completed(raw_path)
    actual_spend, outstanding = _ledger_state(ledger_path)

    # A crash can occur after the append-only response is saved but before settlement.
    for row in completed.values():
        for attempt in row.get("attempts", []):
            reservation_id = attempt.get("reservation_id")
            if reservation_id in outstanding:
                actual = float(attempt.get("actual_cost_usd", 0.0))
                append_jsonl(
                    ledger_path,
                    {
                        "event": "settle",
                        "reservation_id": reservation_id,
                        "sample_id": row["sample_id"],
                        "actual_usd": actual,
                        "cost_source": attempt.get("cost_source", "recovered_from_raw"),
                        "at": utc_now(),
                    },
                )
    actual_spend, outstanding = _ledger_state(ledger_path)
    target_ids = [sample_id(study, task, fmt, condition, index) for index in range(count)]
    unresolved = {key: value for key, value in outstanding.items() if key.split(":attempt:")[0] in target_ids}
    if assume_pending_unbilled and assume_pending_billed:
        raise ValueError("Choose only one interrupted-reservation settlement mode")
    if unresolved and not (assume_pending_unbilled or assume_pending_billed):
        raise ValueError(
            "Unresolved reservations from an interrupted request exist: "
            f"{sorted(unresolved)}. Re-run with --assume-pending-billed to charge the "
            "full conservative reservation, or use --assume-pending-unbilled only after "
            "confirming OpenRouter did not bill/complete them."
        )
    if unresolved:
        for reservation_id, reserved_usd in sorted(unresolved.items()):
            append_jsonl(
                ledger_path,
                {
                    "event": "settle",
                    "reservation_id": reservation_id,
                    "sample_id": reservation_id.split(":attempt:")[0],
                    "actual_usd": float(reserved_usd) if assume_pending_billed else 0.0,
                    "cost_source": (
                        "conservative_interrupted_request_cost"
                        if assume_pending_billed
                        else "user_assumed_unbilled"
                    ),
                    "at": utc_now(),
                },
            )

    write_lock = asyncio.Lock()
    budget_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(concurrency)
    reserve_amount = _reservation_amount(config)
    cap = float(config["budget"]["metered_api_cap_usd"])
    model_config = config["model"]
    max_retries = int(model_config["max_retries"])
    base_delay = float(model_config["retry_base_seconds"])
    counters = {"requested": count, "skipped": 0, "completed": 0, "failed": 0}

    async def reserve(identifier: str, attempt_number: int) -> str:
        # Attempts restart at one after a process crash, so the reservation ID
        # also needs a run-unique suffix to remain append-only across resumes.
        reservation_id = f"{identifier}:attempt:{attempt_number}:{uuid.uuid4().hex}"
        async with budget_lock:
            spent, pending = _ledger_state(ledger_path)
            projected = spent + sum(pending.values()) + reserve_amount
            if projected > cap + 1e-12:
                raise RuntimeError(
                    f"Budget cap would be exceeded: ${projected:.4f} projected > ${cap:.2f} cap"
                )
            append_jsonl(
                ledger_path,
                {
                    "event": "reserve",
                    "reservation_id": reservation_id,
                    "sample_id": identifier,
                    "reserved_usd": reserve_amount,
                    "projected_metered_usd": projected,
                    "at": utc_now(),
                },
            )
        return reservation_id

    async def settle(identifier: str, reservation_id: str, actual: float, source: str) -> None:
        async with budget_lock:
            append_jsonl(
                ledger_path,
                {
                    "event": "settle",
                    "reservation_id": reservation_id,
                    "sample_id": identifier,
                    "actual_usd": actual,
                    "cost_source": source,
                    "at": utc_now(),
                },
            )

    async def one(index: int, client: httpx.AsyncClient) -> None:
        identifier = sample_id(study, task, fmt, condition, index)
        if identifier in completed:
            counters["skipped"] += 1
            return
        async with semaphore:
            attempts: list[dict[str, Any]] = []
            extracted: dict[str, Any] = {
                "final_answer": None,
                "reasoning": None,
                "refusal": None,
                "finish_reason": None,
                "usage": None,
                "response_id": None,
                "returned_model": None,
                "returned_provider": None,
                "openrouter_metadata": None,
            }
            errors: list[str] = []
            terminal_error: str | None = None
            for attempt_index in range(max_retries + 1):
                attempt_number = attempt_index + 1
                reservation_id = await reserve(identifier, attempt_number)
                attempt_record: dict[str, Any] = {
                    "number": attempt_number,
                    "reservation_id": reservation_id,
                    "started_at": utc_now(),
                }
                retry = False
                actual_cost = 0.0
                cost_source = "unbilled_error"
                try:
                    response = await request_func(
                        client,
                        body,
                        {
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                            "X-OpenRouter-Metadata": "enabled",
                        },
                    )
                    attempt_record["http_status"] = response.status_code
                    try:
                        payload = response.json()
                    except (ValueError, json.JSONDecodeError) as exc:
                        if response.status_code >= 400:
                            payload = {"error_text": response.text[:4000]}
                        else:
                            raise ValueError(f"non-JSON success body: {exc}") from exc
                    if response.status_code >= 400:
                        message = json.dumps(payload, ensure_ascii=False)[:4000]
                        terminal_error = f"HTTP {response.status_code}: {message}"
                        retry = response.status_code in TRANSIENT_STATUS_CODES and attempt_index < max_retries
                        errors.append(terminal_error)
                        error_usage = payload.get("usage") if isinstance(payload, dict) else None
                        if isinstance(error_usage, dict) and error_usage:
                            actual_cost, cost_source = _usage_cost(error_usage, config)
                    else:
                        extracted = _extract_response(payload)
                        actual_cost, cost_source = _usage_cost(extracted["usage"], config)
                        terminal_error = None
                except httpx.ConnectError as exc:
                    terminal_error = f"{type(exc).__name__}: {exc}"
                    errors.append(terminal_error)
                    retry = attempt_index < max_retries
                except (httpx.TimeoutException, httpx.NetworkError, httpx.ProtocolError) as exc:
                    terminal_error = f"{type(exc).__name__}: {exc}"
                    errors.append(terminal_error)
                    retry = attempt_index < max_retries
                    # A request that timed out after transmission may still be billed.
                    # Charge the full reservation so retries cannot evade the cap.
                    actual_cost = reserve_amount
                    cost_source = "conservative_unknown_request_cost"
                except (ValueError, json.JSONDecodeError) as exc:
                    terminal_error = f"Malformed response: {exc}"
                    errors.append(terminal_error)
                attempt_record.update(
                    {
                        "ended_at": utc_now(),
                        "error": terminal_error,
                        "retry": retry,
                        "actual_cost_usd": actual_cost,
                        "cost_source": cost_source,
                    }
                )
                attempts.append(attempt_record)
                if retry:
                    await settle(identifier, reservation_id, actual_cost, cost_source)
                    delay = base_delay * (2**attempt_index) * random.uniform(0.8, 1.2)
                    await asyncio.sleep(delay)
                    continue

                record = {
                    "sample_id": identifier,
                    "sample_index": index,
                    "study": study,
                    "task": task,
                    "format": fmt,
                    "condition": condition,
                    "prompt_id": prompt_record["prompt_id"],
                    "prompt": prompt_record["prompt"],
                    "prompt_sha256": prompt_record["prompt_sha256"],
                    "threshold": prompt_record.get("threshold"),
                    "threshold_exact": prompt_record.get("threshold_exact"),
                    "threshold_numerator": prompt_record.get("threshold_numerator"),
                    "threshold_denominator": prompt_record.get("threshold_denominator"),
                    "lower_bound": prompt_record.get("lower_bound"),
                    "upper_bound": prompt_record.get("upper_bound"),
                    "final_answer": extracted["final_answer"],
                    "reasoning": extracted["reasoning"],
                    "refusal": extracted["refusal"],
                    "requested_model": model_config["id"],
                    "requested_provider": model_config.get("provider"),
                    "expected_provider_quantization": model_config.get(
                        "expected_provider_quantization"
                    ),
                    "returned_model": extracted["returned_model"],
                    "returned_provider": extracted["returned_provider"],
                    "settings": settings,
                    "usage": extracted["usage"],
                    "finish_reason": extracted["finish_reason"],
                    "response_id": extracted["response_id"],
                    "openrouter_metadata": extracted["openrouter_metadata"],
                    "attempts": attempts,
                    "errors": errors,
                    "terminal_error": terminal_error,
                    "saved_at": utc_now(),
                }
                async with write_lock:
                    append_jsonl(raw_path, record)
                await settle(identifier, reservation_id, actual_cost, cost_source)
                counters["completed"] += 1
                if terminal_error is not None:
                    counters["failed"] += 1
                return

    timeout = httpx.Timeout(float(model_config["request_timeout_seconds"]))
    async with httpx.AsyncClient(timeout=timeout) as client:
        await asyncio.gather(*(one(index, client) for index in range(count)))
    actual, pending = _ledger_state(ledger_path)
    counters["actual_cost_usd"] = actual
    counters["outstanding_reserved_usd"] = sum(pending.values())
    counters["metered_commitment_usd"] = actual + sum(pending.values())
    return counters


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", choices=("pilot", "main"), required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--format", dest="fmt", choices=FORMATS, required=True)
    parser.add_argument("--condition", choices=CONDITIONS, required=True)
    parser.add_argument("--count", type=int)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    parser.add_argument("--tasks", type=Path, default=ROOT / "tasks.yaml")
    parser.add_argument("--raw", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--concurrency", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--assume-pending-unbilled",
        action="store_true",
        help="Release interrupted reservations only after checking OpenRouter billing.",
    )
    parser.add_argument(
        "--assume-pending-billed",
        action="store_true",
        help="Settle interrupted reservations at their full conservative amount before resuming.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    validate_tasks_file(config, args.tasks)
    tasks = load_tasks(args.tasks)
    base_dir = run_dir(config, args.study)
    prepared_path = args.prepared or base_dir / "prepared" / "prompts.json"
    count = args.count if args.count is not None else int(
        config["studies"][args.study]["samples_per_cell"]
    )
    if count <= 0:
        raise ValueError("--count must be positive")
    prompt_record = _prompt_record(
        config, tasks, args.study, args.task, args.fmt, args.condition, prepared_path
    )
    if args.dry_run:
        per_request = _reservation_amount(config)
        study_total = (
            len(config["studies"][args.study]["tasks"])
            * len(FORMATS)
            * len(CONDITIONS)
            * int(config["studies"][args.study]["samples_per_cell"])
        )
        print(
            json.dumps(
                {
                    "sample_count": count,
                    "reserved_usd_per_attempt": per_request,
                    "planned_study_responses": study_total,
                    "planned_first_attempt_reservation_usd": per_request * study_total,
                    "metered_api_cap_usd": config["budget"]["metered_api_cap_usd"],
                    **prompt_record,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0
    if args.study == "main":
        print(json.dumps({"main_gate": validate_main_gate(config)}, indent=2))
    load_dotenv(ROOT / ".env", override=False)
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required for sampling")
    raw_path = args.raw or base_dir / "raw.jsonl"
    ledger_path = args.ledger or base_dir / "budget_ledger.jsonl"
    concurrency = args.concurrency if args.concurrency is not None else int(
        config["model"]["max_concurrency"]
    )
    if concurrency <= 0:
        raise ValueError("--concurrency must be positive")
    result = asyncio.run(
        collect(
            config=config,
            tasks=tasks,
            study=args.study,
            task=args.task,
            fmt=args.fmt,
            condition=args.condition,
            count=count,
            raw_path=raw_path,
            ledger_path=ledger_path,
            prepared_path=prepared_path,
            api_key=api_key,
            concurrency=concurrency,
            assume_pending_unbilled=args.assume_pending_unbilled,
            assume_pending_billed=args.assume_pending_billed,
        )
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
