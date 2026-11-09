# Exploratory offline scorer combinations

2026-10-09. No API calls, new model outputs, prompt changes, or product edits.

## Methods

All combinations reuse the complete frozen 682-paper scores. Full-pool LLM_then_CE sorts lexicographically by descending LLM grade, then descending CE score. CE50/CE100 selects the first 50/100 by CE before LLM grading; a fixed SHA-256 PMID tie-break handles CE cutoff ties without labels. Both LLM-only and LLM-plus-CE downstream ordering are reported. Exact ties in each final score tuple use expected metrics. Candidate recall and final recall use positives in the original full topic pool as denominator, never only selected candidates.

These are post-hoc development combinations motivated by observed ties. They are exploratory, not preregistered or held-out evidence. Pointwise scores can be reused because each saved LLM request contained only its paper; this does not simulate a batched/context-dependent LLM. LLM call counts are prospective unique paper decisions; no latency or monetary saving is measured by this replay.

## Abstract-label comparison

| Topic | Variant | nDCG@10 | Recall@50 | Candidate recall | LLM decisions |
|---|---|---:|---:|---:|---:|
| CD012347 | CE | 0.731 | 100.0% | 100.0% | 0 |
| CD012347 | LLM | 0.900 | 78.8% | 100.0% | 216 |
| CD012347 | LLM_then_CE | 0.861 | 81.2% | 100.0% | 216 |
| CD012347 | CE50_then_LLM | 0.900 | 100.0% | 100.0% | 50 |
| CD012347 | CE50_then_LLM_then_CE | 0.861 | 100.0% | 100.0% | 50 |
| CD012347 | CE100_then_LLM | 0.900 | 81.2% | 100.0% | 100 |
| CD012347 | CE100_then_LLM_then_CE | 0.861 | 81.2% | 100.0% | 100 |
| CD010558 | CE | 0.576 | 59.5% | 100.0% | 0 |
| CD010558 | LLM | 0.628 | 77.7% | 100.0% | 237 |
| CD010558 | LLM_then_CE | 0.783 | 81.1% | 100.0% | 237 |
| CD010558 | CE50_then_LLM | 0.826 | 59.5% | 59.5% | 50 |
| CD010558 | CE50_then_LLM_then_CE | 0.783 | 59.5% | 59.5% | 50 |
| CD010558 | CE100_then_LLM | 0.684 | 79.1% | 89.2% | 100 |
| CD010558 | CE100_then_LLM_then_CE | 0.783 | 79.7% | 89.2% | 100 |
| CD010753 | CE | 0.687 | 69.0% | 100.0% | 0 |
| CD010753 | LLM | 0.730 | 94.9% | 100.0% | 229 |
| CD010753 | LLM_then_CE | 0.845 | 93.1% | 100.0% | 229 |
| CD010753 | CE50_then_LLM | 0.769 | 69.0% | 69.0% | 50 |
| CD010753 | CE50_then_LLM_then_CE | 0.845 | 69.0% | 69.0% | 50 |
| CD010753 | CE100_then_LLM | 0.735 | 86.2% | 86.2% | 100 |
| CD010753 | CE100_then_LLM_then_CE | 0.845 | 86.2% | 86.2% | 100 |

Full-text inclusion-label metrics are retained in cascade-metrics.json and must be interpreted separately from abstract screening. These are rank-based comparisons with no quote or native feed gate. Candidate truncation losses remain visible even when downstream reranking is excellent.

## Validation

Checked equal original candidate identities, expected-score tie handling, and that final recall never exceeds candidate recall. For CE50 variants, recall@50 equals candidate recall by construction. Scores for CE and raw LLM reproduce the preceding standalone metrics to numerical tolerance. Only three exposed topics with sampled negatives; confirm any preferred combination on unseen topics before product adoption.
