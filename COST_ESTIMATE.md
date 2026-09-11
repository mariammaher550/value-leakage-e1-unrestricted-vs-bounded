# API cost estimate for reproducing Value Leakage

**Current user constraint: $50 total.** See [BUDGET_PLAN.md](</Users/mariam/CascadeProjects/Value Leakage/BUDGET_PLAN.md>) for a proposed focused study within that budget. The full-scope scenarios below remain a reference; they are not the selected plan.

Prepared September 10, 2026. Currency: **USD**. Scope: the six main experiments in [EXPERIMENTS_SETUP.md](</Users/mariam/CascadeProjects/Value Leakage/EXPERIMENTS_SETUP.md>), including E1 trajectory analysis and E5 fairness conditions. The user's later modification and subset are still undecided.

**Planning estimate for the priced portion: $104,282; approximately $125,139 with a 20% execution reserve.** Short-, base-, and long-output scenarios give **$34,932 / $104,282 / $268,689**, before the reserve. These are scenario calculations, not measured usage, a confidence interval, or the authors' reported spend.

**Add U to each scenario:** the subject-generation cost of 2,700 Qwen3.5-35B-A3B responses and 2,700 Kimi K2.5 responses. Both original Tinker routes have been retired. No current price for those exact routes is available; U is unknown, not zero. Their planned evaluation calls are included in the priced subtotal. A fresh reproduction of every original model therefore also requires resolving model access. [Tinker retirement schedule](https://tinker-docs.thinkingmachines.ai/tinker/model-deprecations/).

## 1. What “probes” means here

These experiments use behavioral prompts and sampled responses. They do not train linear probes or other learned probes. Below, a **subject rollout** means one experimental response or completed tool interaction. An **agent session** in E5 contains ten graded questions and can involve several API requests. Judges and candidate generators are additional billable models.

The original counts imply **541,900 subject rollouts/sessions**: 539,900 across E1–E4 and E6, plus 2,000 E5 sessions covering 20,000 grading decisions. This budgeting plan also allocates **1,877,900 evaluation calls** and **20,000 candidate-generation calls**. These evaluation/candidate counts reflect the explicit coverage assumptions below, not a recovered historical API invoice. Tool continuations, failed attempts, and retries add requests.

## 2. Cost by experiment

“Evaluation + candidates” includes the judge passes listed in Section 5. Counts are planned before exclusions. Monetary totals sum unrounded values; displayed rows are rounded.

| Experiment | Subject models/configurations | Planned subject rollouts or sessions | Base generation | Base evaluation + candidates | Base API subtotal |
| --- | --- | ---: | ---: | ---: | ---: |
| E1: Donation Bet | 21 configurations across 16 models; 19 configurations priced | 56,700 | $6,853 + U | $4,914 | **$11,767 + U** |
| E2: AI Bubble | Opus 4.8/4.7/4.6 max; GPT-5.5/5.4 xhigh; Gemini 3.1 Pro high | 126,000 | $32,164 | $3,780 | **$35,944** |
| E3: AGI Tweet | Same six configurations as E2 | 126,000 | $32,164 | $3,780 | **$35,944** |
| E4: Job Offer | Opus 4.7/4.8 high; Fable 5 high; Gemini 3.1 Pro medium; GPT-5.5 high; GPT-5.4 medium | 7,200 | $1,069 | $880 | **$1,949** |
| E5: Agentic Grading | Opus 4.7 adaptive-max; GPT-5.4 high; Haiku 4.5 generates candidates | 2,000 sessions | $1,531 | $191 | **$1,722** |
| E6: Choosing Activities | Opus 4.7/4.8 xhigh and max; GPT-5.5 high and xhigh; Gemini 3.1 Pro high | 224,000 | $13,398 | $3,560 | **$16,957** |
| **Total** | Original main comparison lineups | **541,900** | **$87,178 + U** | **$17,105** | **$104,282 + U** |

E2 and E3 together account for approximately 69% of the priced base budget. Reproducing only a selected experiment at its original sample count can be much cheaper than repeating the full comparison.

| Experiment | Short-output scenario | Base scenario | Long-output scenario |
| --- | ---: | ---: | ---: |
| E1: Donation Bet | $3,824 + U | $11,767 + U | $31,322 + U |
| E2: AI Bubble | $12,264 | $35,944 | $82,261 |
| E3: AGI Tweet | $12,264 | $35,944 | $82,261 |
| E4: Job Offer | $738 | $1,949 | $4,964 |
| E5: Agentic Grading | $550 | $1,722 | $5,088 |
| E6: Choosing Activities | $5,292 | $16,957 | $62,792 |
| **Total before reserve** | **$34,932 + U** | **$104,282 + U** | **$268,689 + U** |
| **Including 20% reserve** | **$41,919 + 1.2U** | **$125,139 + 1.2U** | **$322,426 + 1.2U** |

The reserve is a planning allowance for retries and unexpected usage. It does not make the long-output scenario an upper bound. U is scenario-specific: its eventual value also depends on the token usage and hosting route of the two currently unpriced models.

## 3. Verified token prices

Prices per **one million tokens**, using standard processing, uncached text input, and the indicated provider. No batch, promotional credits, free tier, or cache savings are assumed. The listed GPT-5.6 Sol standard rate is itself currently promotional. All prices were checked on September 10, 2026.

| Model | Input / 1M | Output / 1M | Price source / route |
| --- | ---: | ---: | --- |
| Claude Opus 4.5, 4.6, 4.7, 4.8 | $5.00 | $25.00 | [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| Claude Fable 5 | $10.00 | $50.00 | [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| Claude Sonnet 4.6 — judge | $3.00 | $15.00 | [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| Claude Haiku 4.5 — candidate generator | $1.00 | $5.00 | [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| GPT-5.2 | $1.75 | $14.00 | [OpenAI model page](https://developers.openai.com/api/docs/models/gpt-5.2) |
| GPT-5.4 | $2.50 | $15.00 | [OpenAI model page](https://developers.openai.com/api/docs/models/gpt-5.4) |
| GPT-5.5 | $5.00 | $30.00 | [OpenAI model page](https://developers.openai.com/api/docs/models/gpt-5.5) |
| GPT-5.6 Sol | $4.00 | $20.00 | [OpenAI pricing](https://developers.openai.com/api/docs/pricing) |
| GPT-5.4-mini — activity parser | $0.75 | $4.50 | [OpenAI model page](https://developers.openai.com/api/docs/models/gpt-5.4-mini) |
| Gemini 2.5 Pro | $1.25 | $10.00 | [Google pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-2.5-pro) |
| Gemini 3.1 Pro Preview | $2.00 | $12.00 | [Google pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-pro-preview) |
| Gemini 3.5 Flash | $1.50 | $9.00 | [Google pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash) |
| Qwen3.6-35B-A3B | $0.540 | $1.335 | [Tinker: prefill / sample, 64K route](https://tinker-docs.thinkingmachines.ai/tinker/models/) |
| Kimi K2.6 | $2.205 | $5.490 | [Tinker: prefill / sample, 32K route](https://tinker-docs.thinkingmachines.ai/tinker/models/) |
| Qwen3.5-35B-A3B | Unpriced | Unpriced | [Original Tinker route retired June 12, 2026](https://tinker-docs.thinkingmachines.ai/tinker/model-deprecations/) |
| Kimi K2.5 | Unpriced | Unpriced | [Original Tinker route retired July 12, 2026](https://tinker-docs.thinkingmachines.ai/tinker/model-deprecations/) |
| Qwen3.6-Max appendix grader — conditional preview mapping | $1.30 | $7.80 | [Alibaba Cloud: Singapore, input ≤128K](https://www.alibabacloud.com/help/en/model-studio/qwen3-6-max) |

Qwen3.5-35B-A3B-Base is a different checkpoint from the retired instruction/reasoning model; its listing is not a valid replacement price. The Qwen3.6-Max appendix estimate is conditional on confirming that the original agent's endpoint matches `qwen3.6-max-preview`.

These rates assume each request stays within its standard context tier. Google Pro rates above use input ≤200K; GPT-5.4/5.5 have a higher tier above 272K input. Agent session totals below sum across requests and do not imply that any one request exceeds a tier. If it does, reprice that request/session according to provider rules. [Google tiers](https://ai.google.dev/gemini-api/docs/pricing), [GPT-5.4 tiers](https://developers.openai.com/api/docs/models/gpt-5.4), [GPT-5.5 tiers](https://developers.openai.com/api/docs/models/gpt-5.5).

## 4. Every subject model and experiment

These tables price **subject generation only**. Add the evaluation allocation in Section 5 when selecting a subset. Different reasoning settings are distinct experimental conditions even when the per-token price is unchanged.

### E1 — Donation Bet

Per configuration: 9 questions × (100 baseline + 100 above-good + 100 below-good) = **2,700 responses**. Paper: Figure 4 and Appendix E, pp. 7, 42–44.

| Model | Paper reasoning setting | Responses | Base generation cost |
| --- | --- | ---: | ---: |
| Claude Opus 4.5 | high | 2,700 | $415.80 |
| Claude Opus 4.6 | high | 2,700 | $415.80 |
| Claude Opus 4.6 | max | 2,700 | $820.80 |
| Claude Opus 4.7 | high | 2,700 | $415.80 |
| Claude Opus 4.7 | max | 2,700 | $820.80 |
| Claude Opus 4.8 | high | 2,700 | $415.80 |
| Claude Opus 4.8 | max | 2,700 | $820.80 |
| Claude Fable 5 | high | 2,700 | $831.60 |
| GPT-5.2 | medium | 2,700 | $117.18 |
| GPT-5.4 | medium | 2,700 | $126.90 |
| GPT-5.5 | medium | 2,700 | $253.80 |
| GPT-5.5 | high | 2,700 | $496.80 |
| GPT-5.6 Sol | medium | 2,700 | $170.64 |
| Gemini 2.5 Pro | Not separately labeled | 2,700 | $164.70 |
| Gemini 3.1 Pro | medium | 2,700 | $101.52 |
| Gemini 3.1 Pro | high | 2,700 | $198.72 |
| Gemini 3.5 Flash | high | 2,700 | $149.04 |
| Qwen3.5-35B-A3B | Not separately labeled | 2,700 | Unpriced |
| Qwen3.6-35B-A3B | Not separately labeled | 2,700 | $22.79 |
| Kimi K2.5 | Not separately labeled | 2,700 | Unpriced |
| Kimi K2.6 | Not separately labeled | 2,700 | $93.70 |
| **Total** | **21 configurations** | **56,700** | **$6,852.99 + U** |

Base evaluation allowance: **$234 per configuration**, comprising $81 for extraction/disclosure and $153 for trajectory extraction on 1,800 intervention traces. Across all 21 configurations this is **$4,914**. Extracting trajectories only for selected plots would reduce this allowance.

### E2 and E3 — AI Bubble and AGI Tweet

Each model/task: 3 paraphrases × 7 company conditions × 1,000 samples = **21,000 responses**. The table combines both tasks; the cost per task is also shown. Paper: Table 3 and Appendix F.1, pp. 68–70.

| Model | Reasoning | E2 responses | E3 responses | Generation per task | Generation for both |
| --- | --- | ---: | ---: | ---: | ---: |
| Claude Opus 4.8 | max | 21,000 | 21,000 | $6,384.00 | $12,768.00 |
| Claude Opus 4.7 | max | 21,000 | 21,000 | $6,384.00 | $12,768.00 |
| Claude Opus 4.6 | max | 21,000 | 21,000 | $6,384.00 | $12,768.00 |
| GPT-5.5 | xhigh | 21,000 | 21,000 | $7,644.00 | $15,288.00 |
| GPT-5.4 | xhigh | 21,000 | 21,000 | $3,822.00 | $7,644.00 |
| Gemini 3.1 Pro | high | 21,000 | 21,000 | $1,545.60 | $3,091.20 |
| **Total** | **6 configurations/task** | **126,000** | **126,000** | **$32,163.60** | **$64,327.20** |

Base evaluation allowance: **$630 per model per task**, or **$7,560 across both tasks and all six configurations**.

### E4 — Job Offer

Per configuration: 12 ordered employer/offer pairs × 100 samples = **1,200 responses**. Paper: Figure 9 and Appendix G, pp. 13, 82–83.

| Model | Reasoning | Responses | Base generation cost |
| --- | --- | ---: | ---: |
| Claude Opus 4.7 | high | 1,200 | $186.00 |
| Claude Opus 4.8 | high | 1,200 | $186.00 |
| Claude Fable 5 | high | 1,200 | $372.00 |
| Gemini 3.1 Pro | medium | 1,200 | $45.60 |
| GPT-5.5 | high | 1,200 | $222.00 |
| GPT-5.4 | medium | 1,200 | $57.00 |
| **Total** | **6 configurations** | **7,200** | **$1,068.60** |

Base evaluation allowance: **$146.70 per configuration**, assuming seven extracted papers per response; **$880.20 total**. Actual citation counts vary by model.

### E5 — Agentic Grading

Each session grades ten questions, with four candidate answers per question. Include three Alpaca conditions (default, soft fairness, strict fairness) and one ProofNet condition (default), each with 250 sessions per main grader. Paper: Section 6 and Appendix H, pp. 15–16, 88–95.

| Grader | Reasoning / harness | Dataset and conditions | Sessions | Graded questions | Base agent API cost |
| --- | --- | --- | ---: | ---: | ---: |
| Claude Opus 4.7 | adaptive-max / Claude Code | Alpaca: default + soft + strict | 750 | 7,500 | $562.50 |
| Claude Opus 4.7 | adaptive-max / Claude Code | ProofNet: default | 250 | 2,500 | $437.50 |
| GPT-5.4 | high / Codex | Alpaca: default + soft + strict | 750 | 7,500 | $300.00 |
| GPT-5.4 | high / Codex | ProofNet: default | 250 | 2,500 | $231.25 |
| **Total** | | | **2,000** | **20,000** | **$1,531.25** |

Additional base costs: **$170** for up to 20,000 Haiku 4.5 candidate generations and **$21** for 2,000 Sonnet 4.6 disclosure calls. Candidate budgeting assumes one shared set of 250 trial files per dataset, each with 10 questions × 4 answers; these files are reused across graders and fairness conditions. A smaller unique-question pool or existing candidate cache costs less; independently regenerating each experimental cell costs more. Confirm the original candidate/trial reuse pattern when pinning code.

The displayed labels `claude-opus-3`, `claude-haiku-3.5`, `gpt-4o`, and `gpt-4o-mini` are experimental metadata. **No calls to those four models are needed.** Actual candidate answers come from Haiku 4.5.

Optional appendix Qwen3.6-Max grader: 250 default Alpaca + 250 default ProofNet sessions = **500 sessions / 5,000 decisions**. Conditional on the preview endpoint and ≤128K input per request, the same base token assumptions give **$172.25 generation + $5.25 judging = $177.50 extra**, reusing candidates. This is excluded from the main total. Higher-context pricing or a different original endpoint changes it. [Conditional rate](https://www.alibabacloud.com/help/en/model-studio/qwen3-6-max).

### E6 — Choosing Activities

Per configuration: **2,000 preference ratings + 30,000 choice rollouts** (10,000 each with no tools, time tool, and coin-flip tool). Paper: Section 7 and Appendix I, pp. 16–18, 96–104.

| Model | Reasoning | Preference ratings | Choice rollouts | Base preferences cost | Base choices cost | Base generation total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Claude Opus 4.7 | xhigh | 2,000 | 30,000 | $29.00 | $2,175.00 | $2,204.00 |
| Claude Opus 4.7 | max | 2,000 | 30,000 | $29.00 | $2,175.00 | $2,204.00 |
| Claude Opus 4.8 | xhigh | 2,000 | 30,000 | $29.00 | $2,175.00 | $2,204.00 |
| Claude Opus 4.8 | max | 2,000 | 30,000 | $29.00 | $2,175.00 | $2,204.00 |
| GPT-5.5 | high | 2,000 | 30,000 | $34.00 | $1,375.00 | $1,409.00 |
| GPT-5.5 | xhigh | 2,000 | 30,000 | $34.00 | $2,575.00 | $2,609.00 |
| Gemini 3.1 Pro | high | 2,000 | 30,000 | $13.60 | $550.00 | $563.60 |
| **Total** | **7 configurations** | **14,000** | **210,000** | **$197.60** | **$13,200.00** | **$13,397.60** |

Base evaluation allowance: **$508.50 per configuration / $3,559.50 total**. Local time and coin-flip tools have no paid external API in this plan; tokens generated or reread during their continuations are included in the subject budget.

## 5. Evaluation and candidate costs

The paper identifies the judge roles; exact total historical judge requests are not available in the extracted setup. For a conservative, auditable allowance, this plan judges **every subject output** in E1–E4 for extraction and both disclosure channels, even where a selected analysis needs only intervention/favored outcomes. It budgets E1 trajectories on all intervention traces and E6 parsing/disclosure on choices, not preference ratings. Missing reasoning, refusals, deduplication, and reuse of cached judgments can reduce calls.

| Experiment | Billable stage | Model | Planned calls | Base input / output tokens per call | Base API cost |
| --- | --- | --- | ---: | ---: | ---: |
| E1 | Number/probability extraction | Claude Sonnet 4.6 | 56,700 | 1,800 / 40 | $340.20 |
| E2 | Number/probability extraction | Claude Sonnet 4.6 | 126,000 | 1,800 / 40 | $756.00 |
| E3 | Number/probability extraction | Claude Sonnet 4.6 | 126,000 | 1,800 / 40 | $756.00 |
| E1 | Reasoning disclosure: budget every rollout | Claude Sonnet 4.6 | 56,700 | 5,000 / 100 | $935.55 |
| E1 | Final-response disclosure: budget every rollout | Claude Sonnet 4.6 | 56,700 | 2,000 / 100 | $425.25 |
| E2 | Reasoning disclosure: budget every rollout | Claude Sonnet 4.6 | 126,000 | 5,000 / 100 | $2,079.00 |
| E2 | Final-response disclosure: budget every rollout | Claude Sonnet 4.6 | 126,000 | 2,000 / 100 | $945.00 |
| E3 | Reasoning disclosure: budget every rollout | Claude Sonnet 4.6 | 126,000 | 5,000 / 100 | $2,079.00 |
| E3 | Final-response disclosure: budget every rollout | Claude Sonnet 4.6 | 126,000 | 2,000 / 100 | $945.00 |
| E4 | Reasoning disclosure: budget every rollout | Claude Sonnet 4.6 | 7,200 | 5,000 / 100 | $118.80 |
| E4 | Final-response disclosure: budget every rollout | Claude Sonnet 4.6 | 7,200 | 2,000 / 100 | $54.00 |
| E1 | Trajectory extraction: all intervention traces, all 21 configurations | GPT-5.5 (medium) | 37,800 | 5,000 / 2,000 | $3,213.00 |
| E4 | Paper extraction | Claude Sonnet 4.6 (high) | 7,200 | 4,000 / 4,000 | $518.40 |
| E4 | Paper-description score: 7 papers/response budget | Claude Sonnet 4.6 | 50,400 | 1,000 / 50 | $189.00 |
| E5 | Visible-message disclosure per agent session | Claude Sonnet 4.6 | 2,000 | 3,000 / 100 | $21.00 |
| E5 | Alpaca candidate answers | Claude Haiku 4.5 | 10,000 | 500 / 700 | $40.00 |
| E5 | ProofNet candidate proofs | Claude Haiku 4.5 | 10,000 | 500 / 2,500 | $130.00 |
| E6 | Two parsing calls per choice rollout | GPT-5.4-mini | 420,000 | 1,200 / 150 | $661.50 |
| E6 | Two disclosure calls per choice rollout | Claude Sonnet 4.6 | 420,000 | 1,800 / 100 | $2,898.00 |

Sonnet extraction of probabilities is budgeted without reasoning; Appendix F does not independently restate that setting. E4 extraction explicitly uses high reasoning. GPT-5.4-mini parsing includes an output allowance but its exact reasoning configuration remains to be pinned. The two E6 parser passes follow the inspected [activity configuration](https://github.com/TruthfulAI-research/value_leakage/blob/main/choosing_activities/config.yaml); they are separate from Sonnet disclosure classification.

## 6. Token assumptions and arithmetic

**All token lengths below are planning assumptions, not values measured from the paper.** A reasoning label does not promise a particular token count, and the same text tokenizes differently across models. Use provider-billed tokens when calibrating.

For each row and scenario:

```text
cost_USD = calls × (mean_billable_input_tokens × input_price
                 + mean_billable_output_tokens × output_price) / 1,000,000

For agents and tool rollouts:
mean_billable_input/output = sum across all requests in the completed session
```

Billable output includes charged reasoning/thinking, not just the visible final answer or a reasoning summary. Do not add reasoning twice when an API's output total already includes it. [OpenAI reasoning billing](https://developers.openai.com/api/docs/guides/reasoning), [Gemini thinking-token pricing](https://ai.google.dev/gemini-api/docs/pricing).

### Subject tokens

Entries are **short / base / long** average tokens per rollout/session. “Short” describes the scenario, not a change to the original effort setting or a new enforced output limit.

| Stage | Input tokens | Output tokens, including billable reasoning |
| --- | --- | --- |
| E1–E3, medium | 400 / 800 / 1,600 | 1,000 / 3,000 / 8,000 |
| E1–E3, high | 400 / 800 / 1,600 | 2,000 / 6,000 / 16,000 |
| E1–E3, max or xhigh | 400 / 800 / 1,600 | 4,000 / 12,000 / 32,000, subject to registry caps below |
| E1, unlabeled effort (Gemini 2.5, Qwen, Kimi) | 400 / 800 / 1,600 | 2,000 / 6,000 / 16,000; a budgeting bucket, not an assigned effort setting |
| E4, medium | 500 / 1,000 / 2,000 | 1,000 / 3,000 / 8,000 |
| E4, high | 500 / 1,000 / 2,000 | 2,000 / 6,000 / 16,000 |
| E5, Alpaca session, all three conditions | 30,000 / 100,000 / 300,000 | 3,000 / 10,000 / 30,000 |
| E5, ProofNet session | 80,000 / 250,000 / 800,000 | 6,000 / 20,000 / 60,000 |
| E6, preference rating, every effort | 200 / 400 / 800 | 200 / 500 / 1,500 |
| E6, no-tool choice, high | 250 / 500 / 1,000 | 250 / 1,000 / 4,000 |
| E6, no-tool choice, max or xhigh | 250 / 500 / 1,000 | 500 / 2,000 / 8,000 |
| E6, tool choice, high — whole rollout | 600 / 1,500 / 4,000 | 400 / 1,500 / 6,000 |
| E6, tool choice, max or xhigh — whole rollout | 600 / 1,500 / 4,000 | 800 / 3,000 / 12,000 |

The E1–E4 calculation clips scenario outputs to the inspected registry's output caps: 16,000 by default; 64,000 for Opus 4.7 max, Opus 4.8 max/xhigh, and GPT-5.5 high/xhigh; 20,000 for Gemini 3.1 Pro high and Gemini 3.5 Flash high; 32,000 for Kimi K2.6. Thus the long scenario for Opus 4.6 max and GPT-5.4 xhigh uses **16,000**, not 32,000. These current caps are not proof of historical usage and are not assumed to be fully consumed in the base scenario. [Registry and historical caveats](</Users/mariam/CascadeProjects/Value Leakage/EXPERIMENTS_SETUP.md:310>).

### Judge and candidate tokens

| Stage | Input: short / base / long | Output: short / base / long |
| --- | --- | --- |
| E1–E3 number/probability extraction | 800 / 1,800 / 4,000 | 20 / 40 / 100 |
| E1–E4 reasoning disclosure | 1,500 / 5,000 / 15,000 | 50 / 100 / 250 |
| E1–E4 final-response disclosure | 1,000 / 2,000 / 5,000 | 50 / 100 / 250 |
| E1 trajectory extraction, GPT-5.5 medium | 1,500 / 5,000 / 15,000 | 500 / 2,000 / 6,000 |
| E4 paper extraction, Sonnet high | 2,000 / 4,000 / 9,000 | 1,500 / 4,000 / 10,000 |
| E4 per-paper scoring | 600 / 1,000 / 2,000 | 20 / 50 / 100 |
| E5 visible-message disclosure | 1,500 / 3,000 / 8,000 | 50 / 100 / 250 |
| E5 Haiku Alpaca generation | 300 / 500 / 1,000 | 300 / 700 / 1,500 |
| E5 Haiku ProofNet generation | 300 / 500 / 1,000 | 1,000 / 2,500 / 5,000 |
| E6 each GPT-5.4-mini parsing call | 500 / 1,200 / 3,000 | 50 / 150 / 500 |
| E6 each Sonnet disclosure call | 800 / 1,800 / 6,000 | 50 / 100 / 250 |

Judge input lengths budget the rubric plus the relevant visible answer/reasoning text. They are independent of hidden subject reasoning: a short reasoning summary can be judged cheaply even when the subject incurred many hidden reasoning tokens. Open-model raw traces may instead be much longer.

Example: GPT-5.4 xhigh in **one** probability experiment:

```text
21,000 × (800 × $2.50 + 12,000 × $15.00) / 1,000,000 = $3,822 generation
21,000 × $0.030 evaluation allowance = $630 evaluation
Total = $4,452
```

## 7. Selectable subsets

These are budget illustrations, not a decision about the user's later modification. All costs include the selected cells' base judging allowance and exclude the 20% reserve.

| Scope | Subject count | Base API estimate |
| --- | ---: | ---: |
| E1, GPT-5.4 medium, original samples and all nine questions | 2,700 | $360.90 |
| E1, Opus 4.7 high + GPT-5.5 high, original samples | 5,400 | $1,380.60 |
| E1, same two configurations, 20 samples per question/condition | 1,080 | $276.12 |
| E2, Opus 4.7 max + GPT-5.4 xhigh, original samples | 42,000 | $11,466.00 |
| E2, same two configurations, 100 samples per paraphrase/company cell | 4,200 | $1,146.60 |
| E4, GPT-5.4 medium, original samples | 1,200 | $203.70 |
| E4, all six original configurations | 7,200 | $1,948.80 |
| Reanalyse complete existing subject and judge caches | No new subject samples | $0 model API cost; local compute/storage separate |

Smaller sample counts change precision and the stability of baseline thresholds; they are pilots or reduced reproductions. Retain all necessary control conditions. Candidate-generation costs in E5 do not necessarily scale with the number of graders because candidates can be reused.

The authors' repository describes cached data and judgments for offline analysis. The $0 API option depends on the selected caches actually being complete and usable; it does not produce new independent samples or responses to a changed prompt. [Authors' setup and cached-data instructions](https://github.com/TruthfulAI-research/value_leakage#setup).

## 8. Budget boundaries and next calibration

Included: subject outputs and billable reasoning; E5/E6 continuation-token allowances; specified extraction/disclosure/trajectory passes; shared E5 candidate generation. No learned-probe training or GPU training is part of these main protocols.

Excluded: the user's forthcoming modification; appendix-only raw-CoT runs, additional mitigation/framing/threshold sweeps, capability ratings, activity effort/welfare extensions, Agentic Effort, and the conditional Qwen3.6-Max appendix grader. Taxes, currency conversion, paid infrastructure, researcher time, regional/fast-processing premiums, and cache-write charges are outside these standard-rate totals.

Cached input and eligible batch processing may reduce cost. Savings must be calculated for compatible calls and actual cache hits; a blanket 50% reduction across agent sessions and every provider is not assumed. Anthropic and Google publish separate batch rates. [Anthropic batch pricing](https://platform.claude.com/docs/en/about-claude/pricing), [Google batch pricing](https://ai.google.dev/gemini-api/docs/pricing).

Before approving a large run, replace assumptions with a small calibration sample from the chosen model/task/effort cells. Record input, cached input, output, reasoning-token details, finish status, retries, judge input length, papers per E4 response, and all E5/E6 requests per session. Compute per-cell mean cost, then multiply by the planned cell counts; use tail usage to set the reserve. This document does not authorize or execute that paid calibration.

Changing to a different model, effort level, or lower output cap to save money changes the experimental condition. Reducing unnecessary duplicate judge passes or analysing available caches can save money without changing existing subject outputs.

## 9. Experimental sources

Counts, model lineups, and judge roles come from the supplied [paper PDF](</Users/mariam/CascadeProjects/Value Leakage/Past Work/2607.14345v4.pdf>) and the source-linked [EXPERIMENTS_SETUP.md](</Users/mariam/CascadeProjects/Value Leakage/EXPERIMENTS_SETUP.md>). E1: pp. 7, 42–55; E2/E3: pp. 68–80; E4: pp. 13, 82–87; E5: pp. 15–16, 88–95; E6: pp. 16–18, 96–104. Prices are independently sourced in Section 3. Token lengths, judge coverage, reuse policy, and the 20% reserve are this document's planning assumptions.
