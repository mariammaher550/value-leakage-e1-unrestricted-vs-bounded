# Writing guide: Neel Nanda MATS 12.0 application

Use this guide to turn completed research into an application that makes the question, evidence, and limitations easy to assess. Use [APPLICATION_CRITERIA.md](APPLICATION_CRITERIA.md) for project selection, evaluation criteria, time accounting, and submission checks.

**Source:** all six tabs of [Neel Nanda MATS 12.0 Stream — Admissions Procedure + FAQ](https://docs.google.com/document/d/1p-ggQV3vVWIQuCccXEl1fD0thJOgXimlbBpGk6FI32I/edit), read on 2026-09-10. This is a synthesis of that source, not an official replacement. Suggested outlines, sentence patterns, and project-specific checks below are our operational guidance, not additional application requirements. Linked external papers and example applications were not independently reviewed.

## 1. Write for the actual reading order

1. **Application-form answers:** Neel reads these for every application and uses them as a preliminary filter. Give these the highest communication priority.
2. **Executive summary:** make it independently understandable, with the main finding and enough evidence to assess it.
3. **Research report:** supply the detail needed to understand what happened without reading code.
4. **Code:** encouraged but optional; it supports inspection rather than carrying the explanation.

Do not hide the central finding, the strongest evidence, or the biggest limitation in the report. A reader may never get beyond the form answers. [Source: Application Task Details](https://docs.google.com/document/d/1p-ggQV3vVWIQuCccXEl1fD0thJOgXimlbBpGk6FI32I/edit?tab=t.sa4u6llpnkph).

## 2. Make one or two concrete claims

Organize around the most interesting things you learned. A small, convincing result is stronger than a broad story supported by superficial experiments. An interesting finding should lead the report; do not narrate the project in chronological order.

For each main claim, connect:

- **Question:** what uncertainty did this experiment address, and why does it matter?
- **Setup:** which model, data, intervention, and metric did you use?
- **Observation:** what actually happened, including the relevant comparison?
- **Interpretation:** why does this support the claim?
- **Boundary:** what remains unresolved, and what else could explain it?

Distinguish an observation from your explanation of it. A probe predicting a label does not, by itself, establish that its direction causally mediates the behavior. An intervention changing an answer does not, by itself, establish that it changed the intended concept. These are practical applications of the source's emphasis on matching evidence to claims.

When results are negative or inconclusive, explain the hypothesis, the sensible tests you tried, what failed, and what you learned. Show the reasoning behind a pivot or diagnosis. Do not turn a negative result into a positive one through wording. [Sources: Advice on good applications](https://docs.google.com/document/d/1p-ggQV3vVWIQuCccXEl1fD0thJOgXimlbBpGk6FI32I/edit?tab=t.75rygwi582jr), [What does a good application look like?](https://docs.google.com/document/d/1p-ggQV3vVWIQuCccXEl1fD0thJOgXimlbBpGk6FI32I/edit?tab=t.qtl0g8o3ozvu).

## 3. Application-form answers

Answer the actual question immediately. Use concrete details: model names, the key experiment, the important number, the comparison, and the largest limitation. Explain why the result is interesting instead of calling it important or novel.

An optional drafting scaffold:

> I investigated [specific question] in [model and setting]. I tested [hypothesis] using [experiment and comparison]. I found [result, with a number where meaningful]. This suggests [bounded conclusion], although [main limitation or alternative explanation].

This is a scaffold to fill from verified results, not submission prose to copy verbatim. The source does not provide the complete current form or its field limits; check those in the [linked application form](https://airtable.com/appnMboxg76F1QIDc/pagqu7wWWrUCZkNVI/form) before final drafting.

The source identifies a question asking for **1–3 pieces of evidence that you could do good research in the program**. Pick specific achievements and explain their relevance. Research papers, open-source work, startups, blog posts, and substantial work or class projects can all supply evidence. Credentials are useful only insofar as they demonstrate ability.

## 4. Executive summary

**Source limits:** the Google Doc begins with an executive summary of **1–3 pages, at most 600 words and at most 3 pages**. Around one page including graphs is encouraged. Include graphs; concise bullets are welcome.

Suggested structure:

1. **Problem and motivation:** the precise question and why it is worth investigating.
2. **Main takeaways:** one or two findings, expressed concretely and with appropriate uncertainty.
3. **Key experiments:** roughly one paragraph and graph per central experiment, explaining the test, result, and connection to the takeaway.
4. **Limits:** the biggest unresolved issue and, where useful, the next discriminating experiment.

The first three elements adapt the source's suggested format; the separate limits item implements its broader instruction to communicate limitations clearly. No fixed word budget per section is prescribed.

Assume interpretability research experience, but **no familiarity with this project**. Define project-specific terms, give essential context, and make the summary understandable without following links or reading the report. [Source: Executive Summary Format](https://docs.google.com/document/d/1p-ggQV3vVWIQuCccXEl1fD0thJOgXimlbBpGk6FI32I/edit?tab=t.sa4u6llpnkph).

## 5. Research report

The source does not impose a full-report word or page limit. Use enough detail to make the work assessable, while keeping the main narrative focused. A useful outline is:

1. Executive summary.
2. Raw qualitative examples, immediately after the summary when data or judgment quality is central to the result.
3. Research question and essential background.
4. Setup: models, data, prompts, metrics, and relevant experimental choices.
5. Results organized by finding, with controls and interpretation next to each result.
6. Limitations, failed approaches that affected the conclusion, and next steps.
7. Supporting methods, code link, and time/contribution information where relevant.

Explain why each experiment was worth doing, the hypothesis it tested, and what outcomes would have distinguished competing explanations. Retain failed experiments when they explain your decisions or constrain the conclusion; avoid an exhaustive experiment diary.

Describe data generation or selection, prompt construction, metric definitions, and relevant hyperparameters. Short bullets and small code snippets are useful when clearer than prose. Include details that change how a reader should interpret the results; move secondary material out of the main narrative.

## 6. Figures and qualitative examples

Every central figure should make a specific piece of evidence easy to understand. As a practical checklist:

- Give the figure a descriptive title and label axes, units, conditions, and baselines.
- State the model, dataset or sample, and metric when needed to interpret it.
- Explain what the reader should notice and what conclusion it supports.
- Report uncertainty or variation when measured; do not imply precision that the experiment cannot support.
- Make clear whether the display contains individual examples, an aggregate, or a selected subset.

If synthetic data, an LLM judge, or subjective labels could invalidate the result, personally inspect the data and include **randomly selected raw examples**, ideally just after the executive summary. Show enough context to judge whether the labels or scores make sense. Do not present cherry-picked examples as evidence of typical performance.

The source allows selected examples for a narrowly stated **existence claim**. That does not justify general claims about frequency, reliability, or method superiority. State the selection method and the limited claim. [Sources: Application Task Details](https://docs.google.com/document/d/1p-ggQV3vVWIQuCccXEl1fD0thJOgXimlbBpGk6FI32I/edit?tab=t.sa4u6llpnkph), [Research Advice](https://docs.google.com/document/d/1p-ggQV3vVWIQuCccXEl1fD0thJOgXimlbBpGk6FI32I/edit?tab=t.75rygwi582jr).

## 7. Show verification, not just confidence

Document checks that actually happened:

- Which raw prompts, outputs, transcripts, or labeled examples did you inspect?
- Did you read the code producing each central result?
- Did the report's numbers match the saved experimental outputs?
- Which headline quantities did you independently recompute or spot-check?
- Which simple alternative explanations did you test?
- Which baseline or control could have made the result uninteresting, and what happened?

For each check, state its scope and outcome. Do not write a vague assurance that everything was validated. Never invent inspection counts, tests, experiments, or outcomes.

If a check remains undone, name it as a limitation and weaken the claim where necessary. Neel explicitly values self-awareness under the time limit, and says unverified or misunderstood agent-produced key results can disqualify an application. [Source: Sanity-check your agent](https://docs.google.com/document/d/1p-ggQV3vVWIQuCccXEl1fD0thJOgXimlbBpGk6FI32I/edit?tab=t.75rygwi582jr).

## 8. Voice and LLM assistance

Write the form answers and executive summary yourself, in your own voice. The source encourages LLM use for research, drafting support, brainstorming, critique, and graphs, but explicitly advises against submitting raw LLM-written prose. It describes obviously LLM-written answers as a substantial negative signal and, elsewhere, says documents that read like LLM slop will be rejected.

Use an assistant to identify missing context, confusing sentences, unsupported claims, numerical inconsistencies, and technical inaccuracies. Ask it to challenge the argument. You remain responsible for the experimental choices, interpretation, and final wording.

Practical editing rules derived from that advice:

- Lead with what you found; remove ceremonial introductions.
- Prefer a precise verb and concrete object to broad adjectives.
- Explain why something surprised you, rather than calling it groundbreaking.
- Replace vague claims of rigor with the actual control or check.
- Keep uncertainty local to the claim it qualifies.
- Use headings, bullets, and intuitive explanations where they improve comprehension.
- Do not add complexity or jargon to make a modest result sound more impressive.

## 9. Applying the guide to Value Leakage

The research-problems tab explicitly suggests investigating why a model's values silently shape its answers, where those values intervene, whether the model can disclose the influence or whether it can be turned off, and whether a linear direction predicts and causally mediates it. These are **suggested questions, not established results of this project**. [Source: Science of Model Character](https://docs.google.com/document/d/1p-ggQV3vVWIQuCccXEl1fD0thJOgXimlbBpGk6FI32I/edit?tab=t.knytn7x826kv).

For this project, make clear:

- What operationally counts as value leakage in the chosen task, and how it differs from ordinary task error or an explicit value judgment.
- Whether the phenomenon replicated in the exact model, prompts, and data being studied.
- Whether a result concerns prediction, a causal intervention, disclosure, or mitigation. Do not conflate these.
- How the simplest relevant baseline performs, and whether an intervention changes general answer quality or causes unrelated effects.
- What has been established in the tested setting and what would require broader evidence.

These are proposed ways to implement the source's research principles, not a prescribed experimental protocol.

## 10. Final writing pass

- [ ] Form answers communicate the question, concrete result, interest, and largest limitation without relying on the report.
- [ ] The executive summary is first, self-contained, no more than 600 words, and no more than 3 pages.
- [ ] The narrative develops one or two findings, with readable graphs and supporting evidence.
- [ ] The reader can understand the setup without opening the code.
- [ ] Random raw examples are included where data or judge quality is central.
- [ ] Observations, interpretations, speculation, and unresolved questions are distinguishable.
- [ ] Reported numbers agree with outputs; verification claims describe work actually done.
- [ ] Relevant baselines, alternative explanations, and limitations are visible.
- [ ] Final form answers and summary sound like the applicant and reflect their understanding.
- [ ] Google Doc access and the applicable time rules have been checked using [APPLICATION_CRITERIA.md](APPLICATION_CRITERIA.md).

## Source coverage

| Source tab | Contribution to this guide |
| --- | --- |
| [Key Details](https://docs.google.com/document/d/1p-ggQV3vVWIQuCccXEl1fD0thJOgXimlbBpGk6FI32I/edit?tab=t.0) | Reading priority, common failures, communication and agent responsibility. |
| [Application Task Details](https://docs.google.com/document/d/1p-ggQV3vVWIQuCccXEl1fD0thJOgXimlbBpGk6FI32I/edit?tab=t.sa4u6llpnkph) | Deliverables, summary limits, raw examples, voice, and time boundaries. |
| [Advice on good applications](https://docs.google.com/document/d/1p-ggQV3vVWIQuCccXEl1fD0thJOgXimlbBpGk6FI32I/edit?tab=t.75rygwi582jr) | Narrative, exploration/understanding/distillation, evidence, figures, LLM use, verification. |
| [What does a good application look like?](https://docs.google.com/document/d/1p-ggQV3vVWIQuCccXEl1fD0thJOgXimlbBpGk6FI32I/edit?tab=t.qtl0g8o3ozvu) | Evaluation signals, inconclusive results, background evidence, lessons from examples. |
| [Recommended Research Problems](https://docs.google.com/document/d/1p-ggQV3vVWIQuCccXEl1fD0thJOgXimlbBpGk6FI32I/edit?tab=t.knytn7x826kv) | Current research framing and the Value Leakage questions. |
| [FAQ (Extended)](https://docs.google.com/document/d/1p-ggQV3vVWIQuCccXEl1fD0thJOgXimlbBpGk6FI32I/edit?tab=t.62dwfjn1hlrr) | Confirms broader safety scope and increased emphasis on form answers and agentic research; program logistics are in the companion file. |
