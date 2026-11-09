# Comparing an LLM and a Cross-Encoder for Ranking a Clinical Literature Feed

An offline component comparison for SciSpark Psychiatry. On the same 682 papers across three previously inspected clinical topics, compare a hosted Jina cross-encoder, a pointwise GPT-4o-mini clinical relevance scorer, and exploratory combinations of their saved scores.

This is a separate study from **Attributed Relevance Judgments** and from the private summary-card evaluation pilot. It evaluates ranking, candidate selection, and a separate lexical quote-gate diagnostic. It does not evaluate generated-summary accuracy or clinician benefit.

Read the [article](reports/blog-ce-vs-llm-clinical-feed.md), then the [methods and evidence appendix](reports/blog-ce-vs-llm-clinical-feed-methods.md). The original main-run [protocol](PROTOCOL.md) was frozen before that run's results; the combinations were designed afterward and are exploratory.

## Results in this setting

| Topic | CE nDCG@10 | LLM nDCG@10 | CE Recall@50 | LLM Recall@50 |
|---|---:|---:|---:|---:|
| Depression with COPD | 0.731 | 0.900 | 100.0% | 78.8% |
| Treatment-resistant depression | 0.576 | 0.628 | 59.5% | 77.7% |
| Insomnia | 0.687 | 0.730 | 69.0% | 94.9% |

The LLM had higher nDCG@10 on all three topics. Recall@50 was higher on two topics and lower on one. CE tie-breaking within LLM grades improved nDCG@10 on two topics and lowered it on one. CE candidate cutoffs reduced prospective LLM scoring volume while limiting candidate recall. These are descriptive observations, without a general superiority claim.

## Reproduce the saved-score analysis

Python 3.9 or later; standard library only. Run from this study folder:

```sh
python3 scripts/verify_export.py
python3 scripts/expanded_cascades.py
python3 scripts/verify_blog_ce_llm.py
```

The first command checks the public file manifest, data schemas, input identities, labels, and local links. The second regenerates all 42 combination metric rows and their report. The third independently recomputes the metrics using per-positive rank contributions, checks all 12 standalone rows and quote attrition, and updates the article's verification record. No model calls, API keys, network access, or product checkout are needed.

## Contents and provenance

| Path | Contents |
|---|---|
| `data/` | Topic definitions, exact common LLM prompt/schema with paper placeholders, candidate identities and labels, input/request hashes, export provenance |
| `runs/clinical-expanded-v1/` | Completed CE scores |
| `runs/expanded-clinical-pointwise-v1/` | LLM grades and validation flags, standalone metrics, combination metrics |
| `reports/` | Article, methods appendix, full combination report, verification record |
| `scripts/` | Offline reproduction and verification |
| `LICENSES/`, `NOTICE.md` | Data and prompt attribution |

Exported scores and metrics come from saved October 2026 runs. Labels come from CLEF TAR 2019 review-screening decisions; provenance pins the source revision. The candidate set retains all 82 abstract-stage positives in the available pools and 200 hash-selected negatives per topic. It contains 41 final-inclusion positives.

The public analysis rows omit raw model prose. Paper titles and abstracts are not redistributed here; all 682 submitted CE and LLM paper texts were checked for equality before export, and their hashes are retained. The frozen score/flag projections reproduce numerical analysis, **not new model inference**. Quote-verification flags are preserved from the original run; their lexical checks cannot be independently rerun without the omitted source text and outputs. The exact prompt and output schema are available for inspection, but the private API runners and credentials are not included.

## Limits

Three development topics, sampled negatives, one CE configuration and one LLM configuration, different query representations and instructions, and one LLM output per paper at mixed request times. Candidate retrieval is outside this experiment. Reference labels measure review eligibility rather than clinical usefulness. Quote matching does not establish semantic support. There are no human summary labels or held-out product-validation results in this study.

Code and reports use the repository's MIT license. CLEF labels and the reproduced product prompt retain their own licenses; see [NOTICE.md](NOTICE.md).
