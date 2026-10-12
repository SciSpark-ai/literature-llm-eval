# E3: decide-only Stage A probe (no quotation requirement)

## Controlled change
Seven frozen request pairs differ from `clinical-v1` only in one system-prompt rule. The production rule

> "quote" must be copied VERBATIM from the paper's title or abstract (at least 8 characters) and must be the passage that justifies your grades. If you cannot quote support for a grade above 0, give 0.

was replaced by

> "quote": leave this field as an empty string. Do not extract or copy evidence in this task; grade on your reading of the title and abstract alone.

Same 100 candidates, order, batches, visible text, JSON schema (the required `quote` string field remains, a residual priming cue), temperature 0, output cap 8192, GPT-4.1-mini-2025-04-14. Request equality outside this rule was asserted for all seven requests. All seven batches succeeded; no candidates were ungraded; all 100 `quote` fields came back empty, so every record is zeroed by production verification and only `modelGrade` is analysed. Development topics; one run per condition; descriptive only.

## Results
Abstract-positive counts with raw model grade above 0, and sampled negative controls (10 per topic, not realistic prevalence):

| Topic | Positives | Joint v1 | Contiguous-quote v2 | Decide-only | Negatives graded >0: v1 / v2 / decide |
|---|---:|---:|---:|---:|---|
| CD010558 treatment-resistant depression | 37 | 24 | 19 | 34 | 3 / 0 / 5 |
| CD010753 antidepressants for insomnia | 22 | 22 | 22 | 22 | 1 / 3 / 0 |
| CD012347 depression in COPD | 16 | 16 | 16 | 16 | 6 / 5 / 5 |

Self-gating check. Of the 13 CD010558 positives that the joint prompt graded 0, decide-only grades 10 above 0 (9 at grade 1, 1 at grade 4). Of the 18 graded 0 under the quote variant, 17 become positive (15 at grade 1, 2 at grade 4). One positive (PMID 22070769) is graded 0 in all three runs. All 10 rescued CD010558 records are abstract-positive but content-negative, so they are weak or scope-level matches under the review's own full-text decision.

Grade distribution shift. Removing the quote rule changed the grading scale, not only the floor:

| Run | Positives at grade 0 / 1 / 3 / 4 | Negatives at 0 / 1 / 3 / 4 |
|---|---|---|
| Joint v1 | 13 / 9 / 6 / 47 | 15 / 8 / 1 / 1 |
| Quote v2 | 18 / 16 / 2 / 39 | 17 / 8 / 0 / 0 |
| Decide-only | 3 / 33 / 0 / 39 | 15 / 9 / 0 / 1 |

Decide-only never used grade 3 and moved 15 positives from grade 3 or 4 down to grade 1 (transitions 3 to 1: 6; 4 to 1: 9). At a threshold of grade 2 or higher (dropping "one facet only"), decide-only retains fewer positives than the joint baseline on every topic: CD010558 13 versus 18, CD010753 14 versus 21, CD012347 12 versus 14.

Paired flips. Decide-only versus joint v1 changed the raw grade for 29 of 100 records (positives: 10 up, 15 down; negatives: 2 up, 2 down). Joint v1 versus quote v2 also changed 29 of 100. With one run per condition, the share of these flips due to run-to-run variance is unknown.

Tokens. Decide-only used 42,466 input and 3,924 output tokens, against 42,592 / 6,989 for v1 and 43,012 / 5,725 for v2; the quote field accounts for roughly 30 to 45 percent of output tokens in the joint prompts.

## Interpretation
1. The go/no-go criterion "decide-only recall exceeds joint recall by at least 3 points on at least two of three topics" is not met at the grade-above-0 threshold: the gain is confined to one topic, and there it is dominated by grade-1 partial matches.
2. The quote rule is entangled with the grading scale. Removing it does not simply lift a floor; it changes how the model distributes grades 1 to 4. Any decoupled design must therefore be compared at matched admitted fraction and across thresholds, not at a fixed grade cut.
3. The self-gating mechanism is real on the narrow-population topic (10 of 13 zeros recover), but what it suppresses are weak matches. Whether a clinician feed should surface them is a product question; for review-screening recall they count as misses.
4. Nothing here separates instruction effect from run variance. E4 (repeated runs of both arms) remains the decisive experiment for Direction 2.

## Cost and artifacts
- Estimated model cost at guarded list rates: $0.0232648. Conservative reservation: $0.436711. Shared cumulative reservation: $5.973328 against the $6 internal lane and $10 user ceiling; actual estimated spend across the ledger: $0.334865.
- `runs/clinical-decide-only-v1/`: frozen requests, responses, replayed results. `scripts/clinical_decide_only.mjs` (capture/replay), `scripts/clinical_decide_only_paid.py` (guarded transport; the ranking lane is set to the documented $6), `scripts/clinical_decide_only_compare.py` (paired counts).
- No product source changes. No new human labels. The ledger also records 4o-mini Wiki-rubric calls from a concurrent `controlled_4o_strict_v3.py` job that is not part of this probe.
