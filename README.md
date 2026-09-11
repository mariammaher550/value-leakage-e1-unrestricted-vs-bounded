# Modified E1: unrestricted versus bounded estimates

This repository implements the five-stage experiment in
[`E1_EXPERIMENT_MODIFIED.md`](E1_EXPERIMENT_MODIFIED.md): OpenRouter sampling,
file-based OpenAI judging, threshold/bound preparation, bias metrics, and
regenerable figures.

The nine questions and the unrestricted `accurate` prompt wording are copied
from `TruthfulAI-research/value_leakage` at commit
`f7e5480cfe8abeb64b7007ba24fb0164519c3b68`. The small-pipeline reference is
`adsingh-64/value-leakage` at commit
`16d129859e1f0e281363fb4f5910bcaeea316b10`. Both revisions are frozen in
[`config.yaml`](config.yaml).

## Setup

Python 3.12 is recommended.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
```

Sampling uses only `OPENROUTER_API_KEY`. Do not put the key in a tracked file.

```bash
export OPENROUTER_API_KEY='...'
```

The initial configuration pins `qwen/qwen3.6-35b-a3b` to OpenRouter's
`darkbloom` provider (listed as FP4 when checked on 2026-09-11) with fallbacks
disabled, temperature 1, returned reasoning enabled, and a 16,000-token
completion allowance. The pilot must confirm the
returned provider, reasoning availability, completion behavior, and actual
cost before those settings are retained for the main study.

## Pilot execution

First inspect the exact unrestricted baseline prompt and the conservative cost
reservation. This does not call a model.

```bash
.venv/bin/python sample.py --study pilot --task giraffes --format unrestricted --condition baseline --dry-run
```

Collect the ten fresh baseline responses:

```bash
.venv/bin/python sample.py --study pilot --task giraffes --format unrestricted --condition baseline
```

Export judge files. Each batch contains at most ten records. Judge
`final/*/input.jsonl` using the adjacent, unchanged `instructions.md`, and save
the returned JSONL files under a directory such as `returns/pilot/final/`.

```bash
.venv/bin/python judge.py export --study pilot
.venv/bin/python judge.py import --study pilot --kind final --returned returns/pilot/final/*.jsonl --judge-app 'ACTUAL APP' --judge-model 'ACTUAL MODEL'
```

Freeze the pilot threshold, integer bounds, configuration snapshot, interval
coverage, and all six prompt previews:

```bash
.venv/bin/python prepare.py --study pilot
```

Inspect `runs/pilot/prepared/prompts.json`. Then collect the other five cells;
resume is automatic and never adds replacement sample IDs.

```bash
.venv/bin/python sample.py --study pilot --task giraffes --format unrestricted --condition above_good
.venv/bin/python sample.py --study pilot --task giraffes --format unrestricted --condition below_good
.venv/bin/python sample.py --study pilot --task giraffes --format bounded --condition baseline
.venv/bin/python sample.py --study pilot --task giraffes --format bounded --condition above_good
.venv/bin/python sample.py --study pilot --task giraffes --format bounded --condition below_good
```

Re-export after all 60 responses. The first final-estimate batch is unchanged
and need not be judged again; judge the newly added final batches and every
trajectory batch using each batch's adjacent instructions. Do not pass two
returned files containing the same judge ID in one import. Trajectory export
automatically omits missing and truncated traces. Returned files are copied
byte-for-byte into `runs/pilot/judge_results/returned_unchanged/` during import.

```bash
.venv/bin/python judge.py export --study pilot
.venv/bin/python judge.py import --study pilot --kind final --returned returns/pilot/remaining-final/*.jsonl --judge-app 'ACTUAL APP' --judge-model 'ACTUAL MODEL'
.venv/bin/python judge.py import --study pilot --kind trajectory --returned returns/pilot/trajectory/*.jsonl --judge-app 'ACTUAL APP' --judge-model 'ACTUAL MODEL'
.venv/bin/python metrics.py --study pilot
.venv/bin/python plots.py --study pilot
```

Review `runs/pilot/metrics/pilot_manual_audit_selection.jsonl`: it contains five
seeded-random records from every format/condition cell plus all extraction
failures. Record the human review outcome separately; the script deliberately
labels the selection `selected_not_manually_reviewed` rather than claiming the
review happened. Also inspect `usage_and_provider_audit` in
`runs/pilot/metrics/metrics.json`. Do not begin the main study if its observed
cost projection, remaining judging cost, and money already spent do not fit the
$50 total / $40 metered-API envelope. Revise the uniform sample count explicitly
in `config.yaml` first if necessary. When the review is actually complete, copy
`runs/pilot/pilot_approval.template.json` to
`runs/pilot/pilot_approval.json`, set the three approval fields to `true`, record
the approved main sample count, and add notes. `sample.py` enforces this gate,
the frozen model/provider settings, complete 60-record coverage, and the cost
projection before any main-study request.

## Main study

The main study is intentionally separate under `runs/main/`. Sample and judge
all nine fresh unrestricted baselines before preparation:

```bash
for task in giraffes zills bridge crochet tbc maiden turns orangecars windowdays; do
  .venv/bin/python sample.py --study main --task "$task" --format unrestricted --condition baseline
done
.venv/bin/python judge.py export --study main
.venv/bin/python judge.py import --study main --kind final --returned returns/main/baseline-final/*.jsonl --judge-app 'ACTUAL APP' --judge-model 'ACTUAL MODEL'
.venv/bin/python prepare.py --study main
```

After inspecting and freezing `runs/main/prepared/`, sample the five remaining
cells for every task:

```bash
for task in giraffes zills bridge crochet tbc maiden turns orangecars windowdays; do
  .venv/bin/python sample.py --study main --task "$task" --format unrestricted --condition above_good
  .venv/bin/python sample.py --study main --task "$task" --format unrestricted --condition below_good
  .venv/bin/python sample.py --study main --task "$task" --format bounded --condition baseline
  .venv/bin/python sample.py --study main --task "$task" --format bounded --condition above_good
  .venv/bin/python sample.py --study main --task "$task" --format bounded --condition below_good
done
```

Finally re-export, judge both jobs, and regenerate all results without further
subject-model calls:

```bash
.venv/bin/python judge.py export --study main
.venv/bin/python judge.py import --study main --kind final --returned returns/main/final/*.jsonl --judge-app 'ACTUAL APP' --judge-model 'ACTUAL MODEL'
.venv/bin/python judge.py import --study main --kind trajectory --returned returns/main/trajectory/*.jsonl --judge-app 'ACTUAL APP' --judge-model 'ACTUAL MODEL'
.venv/bin/python metrics.py --study main
.venv/bin/python plots.py --study main
```

## Data contract and safeguards

- `runs/<study>/raw.jsonl` is append-only and stores prompts, returned answers,
  available reasoning, provider/model metadata, usage, errors, and every attempt.
- `budget_ledger.jsonl` reserves a conservative maximum before each request and
  settles the actual reported or token-derived cost. An unresolved reservation
  stops resume rather than risking a duplicate call.
- `prepare.py` accepts exactly the planned number of fresh unrestricted
  baselines for that study, preserves half-integer medians exactly, validates
  both donation outcomes, and refuses to overwrite changed frozen artifacts.
- Judge-facing IDs are stable but opaque, so format and donation labels are not
  leaked to the judge. Import flags missing, duplicate, unknown, and mistyped
  results; bounded estimates are never clipped.
- Primary bias retains every parsed integer even when it violates the bounds.
  Missing directions make a task undefined, while valid directions remain
  equally weighted. Bootstrap intervals keep the sampled thresholds fixed.
- Every PNG/PDF and its plotted CSV/NPZ data regenerates from saved raw/judged
  files; plotting makes no model calls.
