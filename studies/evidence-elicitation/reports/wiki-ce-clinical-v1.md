# Wiki rubric, clinical rubric and cross-encoder: fixed-pool diagnostic

## Scope and controls
This is a three-topic development diagnostic, not an end-to-end or held-out recommendation benchmark. The same 100 candidates surviving Psychiatry's baseline gates were supplied to all methods (26, 44 and 30). They contain 75 abstract-screening positives and 25 sampled negatives. This pool therefore favors high top-k scores and conditions on a clinical prefilter. Seven additional insomnia positives were lost upstream; they are not silently reclassified as irrelevant.

Wiki assessment, engine and contract files were byte-checked against fork baseline `435afcd`. Its native rubric was executed through the production skill runner with temperature explicitly set to zero, no feedback memories, and abstracts truncated to the same 1800 characters visible to Psychiatry. Wiki context maps the same condition/treatment/population facts into a question/topic string; approach is applicable only when population is specified. This adapter is an experimental control, not an unmodified native Wiki run. Different rubric/context framing remains part of the comparison.

LLM model: GPT-4.1-mini-2025-04-14; maximum output 8192; original batch order and sizes. Cross-encoder: jina-reranker-v2-base-multilingual, receiving the equivalent query string and identical title/abstract text. Provider-internal tokenization/truncation is not independently audited. All seven Wiki batches validated and all three CE calls returned one score per candidate. No automatic paid retries.

## Raw relevance ranking
Wiki raw relevance is its applicable 50/30/20 question/topic/approach weighted score before evidence validation and exclusion. Psychiatry uses the raw watch-entry grade, excluding topic-grade blending and quote penalties. CE uses provider relevance score. These are task-relevance rankings, not native final feed scores. Equal scores break by PMID string ascending for every method; coarse LLM grades create ties.

| Method | COPD nDCG@10 | Resistant depression | Insomnia |
|---|---:|---:|---:|
| Wiki raw rubric |1.000|1.000|1.000|
| Cross-encoder |0.861|1.000|1.000|
| Clinical original rubric |0.931|1.000|1.000|
| Clinical contiguous-quote variant |1.000|1.000|1.000|

Binary existing abstract labels, linear gains, ideal ranking within the common pool. These ceiling effects are evidence that this diagnostic sample cannot reliably distinguish rankers. Do not claim Wiki or clinical superiority from three positive-enriched topics. A larger pool with realistic/hard negatives and held-out topics is needed. Review screening labels are not perfect clinical-feed relevance labels.

## Eligibility after each pipeline's checks
| Topic | Positive input to model | Wiki retained | Clinical original retained | Clinical quote variant retained |
|---|---:|---:|---:|---:|
| Depression in COPD |16|16|4|13|
| Treatment-resistant depression |37|23|15|12|
| Antidepressants for insomnia |22|18|6|21|

Wiki uses its dimension-specific quote validation, explicit exclusion and relevance threshold. Clinical uses its quote/match verification and model-design gate before final list quotas. Different native acceptance policies are intentionally included here; this table is not a pure model-accuracy comparison. CE has no calibrated acceptance threshold in this experiment and is not assigned an arbitrary retention number.

Sampled negative controls retained: Wiki 3/0/0 across the three topics; both clinical variants 1/0/0. More positive retention alone does not establish a better tradeoff, and a review exclusion need not imply an irrelevant clinical recommendation.

## Interpretation
Clinical specialization has not demonstrated an across-topic advantage. The quote-instruction variant improves one failure mode but does not replace the need for a general baseline. Preserve raw grades separately from extraction/validation outcomes. Do not claim that quoted evidence checking or LLM recommendation was introduced by the clinical fork: both existed upstream.

## Budget and artifacts
Wiki calls cost an estimated $0.0392944 at the guarded model rates. CE usage was recorded in the shared ledger. Conservative cumulative reservations are $4.391435. The internal ranking allowance was expanded from $4 to $6 to support the already authorized comparisons; the user ceiling remains $10 and the original ledger and uncertain charges are preserved.

Scripts: `wiki_compare.mjs`, `wiki_paid.py`, `clinical_ce.py`, `compare_clinical_rankers.py`. Frozen inputs, requests, responses, per-paper validated Wiki scores, CE scores and descriptive rankings are under `runs/wiki-clinical-v1/`. No product source files or vocabulary structures were changed.

## Next work
Expand candidate pools using existing labels before adding more model configurations: current top-k metrics saturate. Keep development topics separate from later validation. Diagnose full-text-positive versus abstract-positive disagreements and raw matching versus quote failures. Only after the task discriminates rankers should a second model and repeated-run/batch-size experiments be used to test robustness.
