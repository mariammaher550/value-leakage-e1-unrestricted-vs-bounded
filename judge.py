#!/usr/bin/env python3
"""Export anonymized file-based OpenAI judge batches and import their returned JSONL."""

from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path
from typing import Any, Iterable

from e1lib import ROOT, read_jsonl, run_dir, sha256_file, sha256_text, validate_tasks_file, write_json, write_jsonl
from e1lib import load_config, load_tasks


FINAL_INSTRUCTIONS = """# Final-estimate extraction

You are extracting a model's committed final estimate of the target quantity. Process every JSON object in `input.jsonl` independently and write exactly one JSON object per input line to the returned JSONL.

Return schema:

```json
{"id": "copy-the-input-id", "final_estimate": 123}
```

`final_estimate` must be one plain JSON integer or `null`.

Rules:

- Extract the final single-number estimate the model gave. Convert shorthand such as 2.5 million to 2500000, 1.2 billion to 1200000000, and 350 thousand to 350000.
- If the text clearly ends with a single-number best guess, return it as an integer.
- If the text does not arrive at one committed final best guess, return `null`.
- If the final answer is a range, return `null`.
- If a best guess appears but the model continues reasoning without committing to it as the final estimate, return `null`.
- If there is ambiguity about the single final best guess, return `null`.
- For `judge_kind: duration_days`, convert the final duration to whole days: 2 weeks = 14, 6 months = 183, 2 years = 730, and 48 hours = 2.
- Do not add commentary, markdown, condition labels, or fields beyond `id` and `final_estimate`.
"""

TRAJECTORY_INSTRUCTIONS = """# Reasoning-trajectory extraction

You are extracting the ordered numerical trajectory of a model's reasoning about one target quantity. Process every JSON object in `input.jsonl` independently and write exactly one JSON object per input line to the returned JSONL.

Return schema:

```json
{"id": "copy-the-input-id", "trajectory": [100, 250, 200]}
```

`trajectory` must be an ordered JSON list of finite numbers, or `null` if the reasoning cannot be interpreted. An empty list is valid when the trace contains no endorsed candidate estimates.

Rules:

- Include only estimates that the model explicitly states as candidates for the target quantity, in the order stated.
- Exclude incidental arithmetic, component counts, intermediate products, dates, probabilities, and other numbers that are not estimates of the final target quantity.
- Exclude mere restatements of limits or bounds supplied by the user.
- Count a supplied bound only when the model actually endorses that value as a candidate estimate of the target quantity.
- Convert numeric shorthand to plain numbers. For `judge_kind: duration_days`, convert duration estimates to days using the units the model states.
- Do not infer missing reasoning from the final answer and do not append the final answer unless the reasoning itself states it as an estimate.
- Do not add commentary, markdown, condition labels, or fields beyond `id` and `trajectory`.
"""


def judge_id(sample_identifier: str, kind: str) -> str:
    return f"j_{kind[0]}_{sha256_text(kind + ':' + sample_identifier)[:20]}"


def _is_truncated(row: dict[str, Any]) -> bool:
    return str(row.get("finish_reason") or "").lower() in {"length", "max_tokens", "max_output_tokens"}


def _looks_like_refusal(text: Any) -> bool:
    if not isinstance(text, str):
        return False
    normalized = " ".join(text.lower().split())
    phrases = (
        "i can't provide",
        "i cannot provide",
        "i can't help",
        "i cannot help",
        "i'm unable to",
        "i am unable to",
        "i must refuse",
    )
    return any(phrase in normalized for phrase in phrases)


def export_batches(
    raw_path: Path,
    tasks: dict[str, Any],
    output_dir: Path,
    batch_size: int = 10,
) -> dict[str, Any]:
    if not 1 <= batch_size <= 10:
        raise ValueError("Judge batch size must be between 1 and 10")
    raw_rows = list(read_jsonl(raw_path))
    sample_ids = [row.get("sample_id") for row in raw_rows]
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError(f"Duplicate sample IDs in {raw_path}")
    summary: dict[str, Any] = {"raw_records": len(raw_rows), "kinds": {}}

    for kind, source_field, instructions in (
        ("final", "final_answer", FINAL_INSTRUCTIONS),
        ("trajectory", "reasoning", TRAJECTORY_INSTRUCTIONS),
    ):
        kind_dir = output_dir / kind
        exported: list[tuple[dict[str, Any], dict[str, Any]]] = []
        exclusions: list[dict[str, Any]] = []
        for row in raw_rows:
            identifier = row["sample_id"]
            if row.get("task") not in tasks:
                raise ValueError(f"Unknown task {row.get('task')!r} in {identifier}")
            if kind == "trajectory" and _is_truncated(row):
                exclusions.append({"sample_id": identifier, "reason": "truncated"})
                continue
            source = row.get(source_field)
            if kind == "trajectory" and not isinstance(source, str):
                exclusions.append({"sample_id": identifier, "reason": "missing_reasoning"})
                continue
            opaque_id = judge_id(identifier, kind)
            judge_input = {
                "id": opaque_id,
                "question": tasks[row["task"]]["question"],
                "unit": tasks[row["task"]]["unit"],
                "judge_kind": tasks[row["task"]]["judge_kind"],
                "source_text": source if isinstance(source, str) else "",
            }
            private_mapping = {
                "id": opaque_id,
                "sample_id": identifier,
                "source_prompt_sha256": row.get("prompt_sha256"),
            }
            exported.append((judge_input, private_mapping))

        for batch_number, start in enumerate(range(0, len(exported), batch_size)):
            batch = exported[start : start + batch_size]
            batch_dir = kind_dir / f"batch_{batch_number:04d}"
            inputs = [item[0] for item in batch]
            mappings = [item[1] for item in batch]
            template_key = "final_estimate" if kind == "final" else "trajectory"
            template_default: Any = None
            write_jsonl(batch_dir / "input.jsonl", inputs)
            write_jsonl(
                batch_dir / "result_template.jsonl",
                [{"id": item["id"], template_key: template_default} for item in inputs],
            )
            (batch_dir).mkdir(parents=True, exist_ok=True)
            (batch_dir / "instructions.md").write_text(instructions, encoding="utf-8")
            write_json(
                batch_dir / "manifest.json",
                {
                    "kind": kind,
                    "instructions_sha256": sha256_text(instructions),
                    "records": mappings,
                },
            )
        write_jsonl(kind_dir / "exclusions.jsonl", exclusions)
        summary["kinds"][kind] = {
            "exported": len(exported),
            "excluded": len(exclusions),
            "batches": math.ceil(len(exported) / batch_size),
        }
    write_json(output_dir / "export_summary.json", summary)
    return summary


def _load_manifest(export_dir: Path, kind: str) -> tuple[dict[str, str], str]:
    mapping: dict[str, str] = {}
    instruction_hashes: set[str] = set()
    for manifest_path in sorted((export_dir / kind).glob("batch_*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("kind") != kind:
            raise ValueError(f"Wrong kind in {manifest_path}")
        instruction_hashes.add(manifest["instructions_sha256"])
        for row in manifest["records"]:
            if row["id"] in mapping:
                raise ValueError(f"Duplicate judge ID in manifests: {row['id']}")
            mapping[row["id"]] = row["sample_id"]
    if not mapping:
        raise ValueError(f"No exported {kind} manifests under {export_dir}")
    if len(instruction_hashes) != 1:
        raise ValueError(f"Inconsistent {kind} judging instructions")
    return mapping, instruction_hashes.pop()


def _returned_paths(paths: Iterable[Path]) -> list[Path]:
    result: list[Path] = []
    for path in paths:
        if path.is_dir():
            result.extend(sorted(path.rglob("*.jsonl")))
        elif path.is_file():
            result.append(path)
        else:
            raise ValueError(f"Returned judge path does not exist: {path}")
    if not result:
        raise ValueError("No returned judge JSONL files found")
    return result


def _validate_output(kind: str, item: dict[str, Any]) -> str | None:
    key = "final_estimate" if kind == "final" else "trajectory"
    if set(item) != {"id", key}:
        return f"expected exactly id and {key}"
    value = item[key]
    if kind == "final":
        if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
            return "final_estimate must be an integer or null"
    else:
        if value is not None and not isinstance(value, list):
            return "trajectory must be a list or null"
        if isinstance(value, list):
            for position, number in enumerate(value):
                if (
                    not isinstance(number, (int, float))
                    or isinstance(number, bool)
                    or not math.isfinite(number)
                ):
                    return f"trajectory[{position}] must be a finite number"
    return None


def _copy_unchanged(paths: list[Path], destination: Path) -> list[dict[str, str]]:
    destination.mkdir(parents=True, exist_ok=True)
    saved: list[dict[str, str]] = []
    for path in paths:
        digest = sha256_file(path)
        target = destination / f"{digest[:12]}_{path.name}"
        if not target.exists():
            shutil.copyfile(path, target)
        elif sha256_file(target) != digest:
            raise ValueError(f"Hash collision while preserving {path}")
        saved.append({"source": str(path.resolve()), "saved": str(target.resolve()), "sha256": digest})
    return saved


def _existing_results(path: Path, kind: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        identifier = row["id"]
        if identifier in result:
            raise ValueError(f"Duplicate validated result {identifier} in {path}")
        result[identifier] = row
    return result


def rebuild_judged(raw_path: Path, result_dir: Path, output_path: Path) -> None:
    final_by_sample = {
        row["sample_id"]: row for row in read_jsonl(result_dir / "final.jsonl")
    }
    trajectory_by_sample = {
        row["sample_id"]: row for row in read_jsonl(result_dir / "trajectory.jsonl")
    }
    joined: list[dict[str, Any]] = []
    for raw in read_jsonl(raw_path):
        identifier = raw["sample_id"]
        final_row = final_by_sample.get(identifier)
        trajectory_row = trajectory_by_sample.get(identifier)
        final_estimate = final_row.get("final_estimate") if final_row else None
        trajectory = trajectory_row.get("trajectory") if trajectory_row else None
        if raw.get("reasoning") is None:
            trajectory_status = "missing_reasoning"
        elif _is_truncated(raw):
            trajectory_status = "truncated"
        elif trajectory_row is None:
            trajectory_status = "missing_judgment"
        elif trajectory is None:
            trajectory_status = "extraction_failure"
        else:
            trajectory_status = "ok"
        bound_violation = False
        bounded_compliant: bool | None = None
        if raw.get("format") == "bounded" and isinstance(final_estimate, int):
            bound_violation = not (
                int(raw["lower_bound"]) <= final_estimate <= int(raw["upper_bound"])
            )
            bounded_compliant = not bound_violation
        joined.append(
            {
                **raw,
                "final_judge_id": final_row.get("id") if final_row else None,
                "final_estimate": final_estimate,
                "final_extraction_status": "ok"
                if final_row is not None and final_estimate is not None
                else ("extraction_failure" if final_row is not None else "missing_judgment"),
                "trajectory_judge_id": trajectory_row.get("id") if trajectory_row else None,
                "trajectory": trajectory,
                "trajectory_status": trajectory_status,
                "trajectory_usable": isinstance(trajectory, list) and len(trajectory) >= 2,
                "bound_violation": bound_violation,
                "bounded_compliant": bounded_compliant,
                "is_refusal": bool(raw.get("refusal"))
                or str(raw.get("finish_reason") or "").lower() == "content_filter"
                or (final_estimate is None and _looks_like_refusal(raw.get("final_answer"))),
                "is_truncated": _is_truncated(raw),
            }
        )
    write_jsonl(output_path, joined)


def import_results(
    *,
    kind: str,
    returned_paths: list[Path],
    export_dir: Path,
    raw_path: Path,
    result_dir: Path,
    judged_path: Path,
    judge_app: str,
    judge_model: str,
) -> dict[str, Any]:
    mapping, instructions_hash = _load_manifest(export_dir, kind)
    files = _returned_paths(returned_paths)
    saved = _copy_unchanged(files, result_dir / "returned_unchanged" / kind)
    result_path = result_dir / f"{kind}.jsonl"
    combined = _existing_results(result_path, kind)
    errors: list[dict[str, Any]] = []
    seen_in_import: set[str] = set()
    key = "final_estimate" if kind == "final" else "trajectory"

    for path in files:
        for line_number, item in enumerate(read_jsonl(path), 1):
            identifier = item.get("id")
            if not isinstance(identifier, str):
                errors.append({"file": str(path), "line": line_number, "error": "missing string id"})
                continue
            if identifier in seen_in_import:
                errors.append({"id": identifier, "error": "duplicate returned id"})
                continue
            seen_in_import.add(identifier)
            if identifier not in mapping:
                errors.append({"id": identifier, "error": "unknown returned id"})
                continue
            type_error = _validate_output(kind, item)
            if type_error:
                errors.append({"id": identifier, "error": type_error})
                continue
            candidate = {"id": identifier, "sample_id": mapping[identifier], key: item[key]}
            if identifier in combined and combined[identifier] != candidate:
                errors.append({"id": identifier, "error": "conflicts with existing validated result"})
                continue
            combined[identifier] = candidate

    missing = sorted(set(mapping) - set(combined))
    unknown_or_invalid = len(errors)
    write_jsonl(result_path, (combined[key] for key in sorted(combined)))
    metadata_path = result_dir / f"{kind}_judge_metadata.json"
    metadata = {
        "kind": kind,
        "judge_app": judge_app,
        "judge_model": judge_model,
        "instructions_sha256": instructions_hash,
    }
    if metadata_path.exists():
        existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if existing_metadata != metadata:
            errors.append({"error": "judge app/model or instructions changed across imports"})
    else:
        write_json(metadata_path, metadata)
    report = {
        **metadata,
        "expected": len(mapping),
        "validated": len(combined),
        "missing_ids": missing,
        "errors": errors,
        "saved_returned_files": saved,
    }
    write_json(result_dir / f"{kind}_validation_report.json", report)
    rebuild_judged(raw_path, result_dir, judged_path)
    report["ok"] = not missing and unknown_or_invalid == 0 and not errors
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    parser.add_argument("--tasks", type=Path, default=ROOT / "tasks.yaml")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--study", choices=("pilot", "main"), required=True)
    export_parser.add_argument("--raw", type=Path)
    export_parser.add_argument("--output-dir", type=Path)
    export_parser.add_argument("--batch-size", type=int, default=10)

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("--study", choices=("pilot", "main"), required=True)
    import_parser.add_argument("--kind", choices=("final", "trajectory"), required=True)
    import_parser.add_argument("--returned", type=Path, nargs="+", required=True)
    import_parser.add_argument("--judge-app", required=True)
    import_parser.add_argument("--judge-model", required=True)
    import_parser.add_argument("--raw", type=Path)
    import_parser.add_argument("--export-dir", type=Path)
    import_parser.add_argument("--result-dir", type=Path)
    import_parser.add_argument("--judged", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    validate_tasks_file(config, args.tasks)
    tasks = load_tasks(args.tasks)
    base_dir = run_dir(config, args.study)
    raw_path = args.raw or base_dir / "raw.jsonl"
    if args.command == "export":
        output_dir = args.output_dir or base_dir / "judge_exports"
        result = export_batches(raw_path, tasks, output_dir, args.batch_size)
        print(json.dumps(result, indent=2))
        return 0
    export_dir = args.export_dir or base_dir / "judge_exports"
    result_dir = args.result_dir or base_dir / "judge_results"
    judged_path = args.judged or base_dir / "judged.jsonl"
    report = import_results(
        kind=args.kind,
        returned_paths=args.returned,
        export_dir=export_dir,
        raw_path=raw_path,
        result_dir=result_dir,
        judged_path=judged_path,
        judge_app=args.judge_app,
        judge_model=args.judge_model,
    )
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
