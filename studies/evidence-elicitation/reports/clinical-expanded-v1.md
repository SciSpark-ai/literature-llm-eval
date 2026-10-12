# Expanded labelled clinical pool: preparation and partial CE result

## Frozen selection
Same three exposed development topics. Retain every abstract-positive reference paper and expand controls from 10 to 200 per topic using the original SHA-based order. All earlier selected records remain included. No model scores or failures were used to select additional controls.

| Topic | Positive | Negative controls | Total |
|---|---:|---:|---:|
| CD012347: depression in COPD |16|200|216|
| CD010558: treatment-resistant depression |37|200|237|
| CD010753: antidepressants for insomnia |29|200|229|

682 unique PMIDs, 570 additional public records fetched, no missing metadata. Original 112-record snapshot reused. Snapshot hashes and retrieval URLs are recorded. Existing abstract labels are primary and full-text labels secondary. Review exclusion does not necessarily mean irrelevant to a clinician.

Common candidate inputs precede the psychiatry domain/design gates. All rankers must see the same pool; native filters can be evaluated as a separate pipeline contrast. Production parser and cleaner were used, with title plus first 1800 abstract characters supplied for ranking. These remain selected development pools, not complete source pools or independent held-out topics.

## Execution status
The initial full-topic CE request exceeded the local 150 KB guard and was rejected before any provider call. The guard was retained; batches were fixed at 40 documents. Model: jina-reranker-v2-base-multilingual. Scores are combined as query-document relevance scores across batches; batch-invariance has not independently been measured.

CD012347 completed. The next topic encountered HTTP 429. No automatic retry occurred. Cached successful calls and the unknown-cost failed request reservation remain in the shared budget ledger. CD010558 and CD010753 have no complete expanded CE results and must not be included as completed runs or zeros.

| Completed topic | nDCG@10 | Positive in top 10 | Positive in top 50 | Recall@50 |
|---|---:|---:|---:|---:|
| CD012347 |0.7313|7/10|16|1.000|

Metrics use binary abstract labels; ties break by PMID string. nDCG@10 and Recall@50 independently checked with pytrec_eval. Do not compare the numeric change with the earlier filtered small pool as a model regression: both pool composition and prefilter exposure changed.

## Budget and next work
Conservative shared reservations: $4.500162, within the unchanged $10 ceiling and $6 internal lane. No expanded-pool LLM comparison has been executed. Preserve incomplete status; provider recovery and an explicit audited retry policy are needed before finishing CE. Then run the Wiki and clinical rubrics on the same frozen candidates, budget-checking requests before calls. Further model tuning should wait for a discriminating comparison.

Artifacts: `runs/clinical-expanded-v1/` includes config, metadata, common candidates, available CE results and metrics. Scripts: `clinical_expand.py`, `clinical_expanded_parse.mjs`, `clinical_expanded_ce.py`, `clinical_expanded_metrics.py`. No product code or vocabulary architecture was changed.
