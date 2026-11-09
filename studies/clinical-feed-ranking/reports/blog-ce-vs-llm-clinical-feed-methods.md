# Methods and evidence: CE versus LLM in a clinical literature feed

Companion to [the article](blog-ce-vs-llm-clinical-feed.md). Prepared from saved experiment artifacts on 2026-10-11; public evidence package prepared on 2026-11-08. Links below resolve within this study.

## Scope and provenance

The main comparison is `expanded-clinical-pointwise-v1`, paired with completed CE scores from `clinical-expanded-v1`. It is distinct from the earlier 60-paper pilot, TREC-COVID retrieval experiments, and later topic inventories. No newly identified topics are represented as completed ranking tests.

| Item | Setting or qualification |
|---|---|
| Topics | CD012347, CD010558, CD010753; previously inspected development topics |
| Candidate selection | All 82 available abstract positives plus 200 hash-selected abstract negatives per topic; 682 records total |
| Original reference-pool sizes | 1,098; 2,815; 2,539 respectively |
| Filtering | Common candidate pool before domain filtering; no inherited psychiatry prefilter |
| Submitted paper text | Identical title and first 1,800 abstract characters in both arms |
| CE | Hosted `jina-reranker-v2-base-multilingual`; provider weights revision not pinned |
| CE batching | Batch size 40 for the first 216 records, then 20 for the remaining 466 after rate-limit recovery |
| LLM | `gpt-4o-mini-2024-07-18`, temperature 0, output cap 8,192 tokens |
| Prompt | Clinical-original evidence-producing scorer with the common single-object output adapter; one paper per request |
| Completion | 682 assessments: 63 exact cached requests reused and 619 new calls |
| Replication | One observation per paper/configuration in this comparison, across mixed request times; not a repeated-run stability test |
| Main output | Raw relevance grade 0–4; no post-hoc entry or quote gate applied to ranking |
| Labels | Abstract-stage labels primary; full-text inclusion labels secondary; neither is a clinician-usefulness label |
| Experimental control | Same paper pool and submitted text; different query representation and instructions, so not a pure architecture comparison |

Equal submitted text does not guarantee equal effective model context: provider tokenization and internal truncation may differ. Temperature 0 is not a guarantee of deterministic output. Prompt choice followed earlier exposed development experiments.

The clinical rubric uses condition, treatment, and available population information. It should not be described as complete PICO eligibility enforcement. Grade 4 denotes a close condition/population and treatment match; 3 allows related populations, subtypes, or treatment classes; 2 denotes partial related matching; 1 a single-facet match; 0 no match. The scorer also requests quotations, so quote generation may influence the raw decision even though the later quote validator is excluded from ranking.

## Metrics and ties

All relevance labels used here are binary. nDCG@10 uses logarithmic rank discounts and an ideal ranking based on the positives in the original topic pool. Recall denominators always use that full pool, including when a cascade retains only 50 or 100 candidates.

For exact score ties, expected gain at each occupied position equals the fraction of positives in the tie group. This yields the expected metric over uniformly random within-group permutations. Both CE and LLM ties receive this treatment. These expectations are not uncertainty intervals or averages over repeated LLM runs.

For CE candidate cutoffs only, ties are resolved by SHA-256 of `cascade-v1:` plus PMID, without labels. Final-score ties then use expected metrics.

## Secondary endpoint: final-inclusion labels

These are nDCG@10 scores against full-text inclusion labels, although models receive only the submitted title and truncated abstract.

| Topic | CE | LLM | LLM with CE tie-break |
|---|---:|---:|---:|
| Depression with COPD | 0.621 | 0.800 | 0.788 |
| Treatment-resistant depression | 0.195 | 0.209 | 0.325 |
| Insomnia | 0.469 | 0.514 | 0.599 |

The lower final-inclusion result on treatment-resistant depression illustrates endpoint sensitivity. It is not evidence that all excluded records are useless to clinicians, nor a test of full-text reasoning.

## Offline cascade interpretation

The combinations reuse saved pointwise scores. `LLM_then_CE` orders by descending LLM grade and then descending CE score. `CE50_then_LLM_then_CE` first truncates to the CE top 50 and then applies the same ordering. Top-100 and LLM-only downstream variants were also completed; see the full [cascade report](expanded-cascade-comparison.md).

Because each saved LLM request sees one paper independently, this replay isolates selection and ordering without new requests. It does not measure live orchestration, latency, retries, repeated-output variation, or actual financial savings. The `llm_calls` field in the replay artifact means prospective unique paper decisions, not API calls made during replay.

For a top-50 candidate set, Recall@50 equals candidate recall by construction. All candidates are already in those fifty positions. This is why reranking cannot fix candidate-stage omissions.

The combinations were motivated by observed ties and are exploratory. There are no held-out topic-level estimates, confidence intervals supporting generalization, or significance claims in the blog.

## Quote attrition

| Abstract-stage positives | Count |
|---|---:|
| Before entry decisions | 82 |
| After raw entry decisions | 77 |
| After entry and lexical quote validation | 72 |

There were also 179 abstract-stage negatives after the entry and quote gates. These are negatives under the review's screening labels, not independently confirmed irrelevant clinical feed items. Quote validation checks lexical source matching; no semantic-entailment or generated-summary accuracy claim follows from it.

## Evidence map

| Blog claim or method | Saved evidence |
|---|---|
| Frozen main-run settings | [Protocol](../PROTOCOL.md), [request template](../data/llm-request-template.json) |
| Pool selection and inputs | [Candidate identities and labels](../data/pool-config.json), [submitted-text hashes](../data/input-manifest.json), [CE queries and LLM interests](../data/topics.json) |
| CE scores | [Complete CE outputs](../runs/clinical-expanded-v1/ce-results-complete.json) |
| LLM grades, labels, entry and quote flags | [Analysis rows](../runs/expanded-clinical-pointwise-v1/analysis.json) |
| Standalone metrics and attrition | [Metrics](../runs/expanded-clinical-pointwise-v1/metrics.json) |
| All cascade variants and both label types | [Cascade metrics](../runs/expanded-clinical-pointwise-v1/cascade-metrics.json), [cascade calculation script](../scripts/expanded_cascades.py) |
| Input and source provenance | [Export transformations and source hashes](../data/export-provenance.json), [label provenance](../data/label-provenance.json) |
| Independent numerical check for this article | [Verification script](../scripts/verify_blog_ce_llm.py), [verification record](blog-ce-vs-llm-verification.json) |

The verification script reads existing outputs and checks expected ranking metrics independently using per-document possible rank positions. It makes no model calls and does not overwrite experiment outputs. Source hashes in the verification record identify the checked files.

The public package supports saved-score reproduction. It omits paper text, raw model prose, and private model-call runners. Quote flags are preserved observations, not recomputed semantic or lexical judgments. Candidate texts were checked for equality between CE and LLM inputs before export; their hashes and a redacted request template are retained.

External context: [CLEF TAR task](https://github.com/CLEF-TAR/tar/tree/master/2019-TAR/Task2) and [Jina model card](https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual). The blog's numerical findings come from the local experiment artifacts, not those external sources.
