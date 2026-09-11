# Final-estimate extraction

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
