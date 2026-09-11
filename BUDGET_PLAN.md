# A research plan within a $50 budget

User's total available budget: **$50**. Prepared September 10, 2026. This is a recommendation for discussion, not a selected modification or permission to spend.

## Recommendation

Combine the two proposed approaches: select **Donation Bet (E1)** and use **Qwen3.6-35B-A3B as the primary model**. It is open-weight and was already evaluated in the paper, so this can be a reduced reproduction using an original model. Preserve funds for the user's forthcoming modification. Add a second model only if a cross-model comparison is central to the question.

The preferred initial question is: **Does the original donation framing shift numerical estimates on these nine questions, and how does that shift change under the user's modification?** The modification has not yet been specified.

The earlier roughly $104K scenario in [COST_ESTIMATE.md](</Users/mariam/CascadeProjects/Value Leakage/COST_ESTIMATE.md>) covers all main model/configuration comparisons and broad evaluation passes. It is not the minimum cost of meaningful research. In particular, the $361 GPT-5.4 Donation Bet example included trajectory and disclosure judging. Those costs are unnecessary for a study restricted to numerical bias.

## Comparing the approaches

| Approach | Assessment |
| --- | --- |
| One main experiment, a small number of original closed models, fewer samples | Scientifically viable for a narrow claim, especially a large known effect. Fewer samples make small changes harder to distinguish, and costly reasoning leaves less room for follow-up. |
| One main experiment using hosted open-weight models | Better sample count per dollar and possible access to raw reasoning. Using a new model is a generalization study; choosing Qwen3.6 retains an original subject model. |
| Reanalyse authors' cached outputs, then run a focused new comparison | Useful preparation with zero new model API cost if the required subject/judge caches are available. Original cached results provide context, but a fresh original condition on our endpoint remains necessary for a fresh intervention comparison. |

Donation Bet has a numerical endpoint and symmetric above/below conditions. That makes it easier to score cheaply than Job Offer's citation/framing pipeline. The company tasks introduce developer/company interpretation when changing model families. Agentic Grading adds harness and multi-request costs. Choosing Activities is a reasonable fallback, but its preference stage, pair sampling, and tool conditions add setup work.

## Why a reduced run can be meaningful

Figure 4 reports **bias approximately 0.27 for Qwen3.6-35B-A3B**, corresponding to an approximately **63.5% favored-outcome rate** under the definition `bias = 2 × p_good - 1`. This supports using it to check a previously observed effect; it does not guarantee replication on today's endpoint. [Supplied paper, p. 7](</Users/mariam/CascadeProjects/Value Leakage/Past Work/2607.14345v4.pdf>).

With 50 responses for each of the two donation directions on all nine questions, there are **900 intervention responses per model/variant**. An illustrative independent-Bernoulli calculation gives at most about **±3.3 percentage points** for a 95% interval on the favored-outcome rate, or **±0.065 on bias**. These are conditional sampling-noise calculations for the fixed questions and thresholds, not guaranteed final confidence intervals.

For two independently sampled variants with 900 intervention responses each, the same approximation gives roughly **0.13 bias units** as an 80%-power detectable change at two-sided 5% significance. Smaller changes may be inconclusive. Task heterogeneity, parse failures, shared estimated thresholds, and the actual analysis affect precision. Use per-question results and stratified resampling; repeated generations do not create hundreds of independent questions.

A useful outcome can be a reproducible shift, a clear boundary on an intervention's effect, or a well-supported failure to reproduce. A non-significant result by itself does not establish absence of bias. Save all nine questions and both donation directions rather than selecting favorable results.

## Open-weight model costs

Comparison unit: **one reduced E1 reproduction with 1,350 subject responses**:

- Nine questions.
- 50 no-donation baseline samples per question.
- 50 above-good and 50 below-good samples per question.
- No future modification included in this comparison table.

Assume **800 input and 6,000 output tokens per subject response**, including charged thinking. This is a planning scenario, not measured usage. Keep Qwen thinking enabled as in the original route. For new GPT-OSS comparisons, medium effort is a proposed starting setting, not a paper setting.

“Core total” adds **$8.10** for one original Sonnet 4.6 numerical-extraction call per response, assuming 1,800 input / 40 output tokens per judge call. It excludes trajectory and disclosure classification. [Sonnet prices: $3 input / $15 output per million](https://platform.claude.com/docs/en/about-claude/pricing).

| Model and provider | In original E1? | Input / output price per 1M | Subject generation | Core total | Role |
| --- | --- | --- | ---: | ---: | --- |
| [Qwen3.6-35B-A3B — Tinker](https://tinker-docs.thinkingmachines.ai/tinker/models/) | Yes | $0.54 / $1.335 | $11.40 | **$19.50** | Primary recommendation; original paper route |
| [Qwen3.6-35B-A3B — Alibaba Frankfurt](https://www.alibabacloud.com/help/en/model-studio/qwen3-6-35b-a3b) | Yes; different provider | $0.248 / $1.485 | $12.30 | **$20.40** | Fallback route; document serving differences |
| [gpt-oss-120b — Fireworks](https://docs.fireworks.ai/serverless/pricing) | No | $0.15 / $0.6 | $5.02 | **$13.12** | Preferred additional model if generalization matters |
| [gpt-oss-20b — Groq](https://console.groq.com/docs/model/openai/gpt-oss-20b) | No | $0.075 / $0.3 | $2.51 | **$10.61** | Cheapest listed comparison; first check task comprehension |
| [Kimi K2.6 — Fireworks](https://docs.fireworks.ai/serverless/pricing) | Yes; different provider | $0.95 / $4 | $33.43 | **$41.53** | Consumes too much of $50 for a first choice |

Qwen3.6 and GPT-OSS have publicly available weights under Apache 2.0 licenses. Hosting still costs money; calling their APIs does not require purchasing or renting a dedicated GPU. [Qwen model card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B), [GPT-OSS model card](https://huggingface.co/openai/gpt-oss-120b).

Prices were checked on September 10, 2026, using standard uncached rates without free credits or batch discounts. These are usage costs, not verified minimum account deposits. Confirm account eligibility, any minimum purchase, tax, and currency charges before funding a provider. Fireworks lists Qwen3.6-35B-A3B as **not serverless-supported**, so its on-demand GPU deployment is not the Qwen route recommended here. [Fireworks Qwen listing](https://fireworks.ai/models/fireworks/qwen3p6-35b-a3b).

Model names alone do not establish identical inference: pin the checkpoint where possible and record provider, quantization when disclosed, chat template, reasoning mode, temperature, and output cap. New-model results support claims about those models rather than about the paper's closed models.

## Proposed $50 allocation

Use **one primary model, Qwen3.6-35B-A3B through Tinker**, and plan around 50 samples per question/condition only if token calibration supports it.

| Item | Subject responses | Base allowance |
| --- | ---: | ---: |
| Original no-donation baseline, 9 × 50 | 450 | $3.80 |
| Original above-good and below-good, 9 × 2 × 50 | 900 | $7.60 |
| Future modified above-good and below-good, 9 × 2 × 50 | 900 | $7.60 |
| Sonnet 4.6 numerical extraction for all 2,250 outputs | — | $13.50 |
| **Estimated core study** | **2,250** | **$32.49** |
| Small token/parser calibration allowance | Additional calibration only | $3.00 |
| Remaining reserve for longer outputs, failures, extra controls, and charges | — | $14.51 |
| **Total budget envelope** | | **$50.00** |

Row rounding produces a one-cent difference; the unrounded subject estimate is $18.9945. Alibaba Frankfurt gives a comparable **$33.99 core estimate**, leaving approximately $13.01 after a $3 calibration allowance.

The future-comparison row is **conditional**: it assumes one modified variant with two donation directions, similar token usage, and an unchanged no-donation baseline that can be shared. If the modification changes the baseline distribution, prompt length, or requires more conditions, revise this allocation. A second fresh baseline of 450 samples alone would add approximately $6.50 at the base assumptions. If it requires activations, training, or interventions inside the model, this hosted behavioral budget no longer describes the setup.

Preserve the paper's numerical judge, including its documented parsing limitations, and manually audit a small sample plus ambiguous cases. Keep the original subject prompts; forcing JSON or short answers would itself alter them. Save available reasoning for inspection, but do not pay for GPT-5.5 trajectory extraction or full Sonnet disclosure classification in this first study. The primary claim concerns numerical bias; it is not a reproduction of the complete covertness analysis.

For a closed-model alternative, Gemini 3.1 Pro medium at **20 samples per question/condition** would give 540 original responses plus 360 modified responses. Assuming 800 input / 3,000 output subject tokens and the same numerical judge, the core estimate is **$39.24**, before calibration and reserves. Its paper E1 bias is approximately 0.80, so even fewer responses may reveal the original effect, but the future intervention comparison is less precise. [Google standard rates: $2 / $12 per million](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-pro-preview), [paper Figure 4](</Users/mariam/CascadeProjects/Value Leakage/Past Work/2607.14345v4.pdf>).

## Staying within $50

The base scenario is not a cost ceiling. For example, at 800 input / 16,000 output subject tokens, the 2,250-response Qwen plan plus the same extraction allowance becomes approximately **$62.53**. Token calibration is therefore necessary before committing to the sample count.

Choose counts from observed cost and completion rates, before inspecting confirmatory effects. If needed, reduce uniformly to 25 samples per question/condition: 1,125 subject responses for the same five-cell design, with a base core estimate of **$16.25** and the 16K-output illustration approximately **$31.27**. This preserves conditions and leaves room for extra controls, while reducing precision. Keep calibration separate if baseline thresholds or prompts change.

For any later implementation, maintain a local budget ledger that includes pending requests and retry allowances; reserve each batch's possible cost before dispatch. Target at most about $40 in metered API usage if the remaining $10 may be needed for charges and uncertainty, and enforce the user's total $50 ceiling. Do not assume a prepaid balance automatically stops spending: Fireworks documents postpaid overages after credits are depleted. [Fireworks billing](https://docs.fireworks.ai/faq-new/billing-pricing/what-happens-when-i-finish-my-1-dollar-credit).

No paid requests, purchases, or experiment runs were made while preparing this recommendation.

