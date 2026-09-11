# Reasoning-trajectory extraction

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
