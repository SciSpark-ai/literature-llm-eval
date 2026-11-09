# Comparing an LLM and a Cross-Encoder for Ranking a Clinical Literature Feed

*An offline comparison of two ranking configurations and their combinations on 682 topic–paper records across three clinical topics.*

SciSpark Psychiatry retrieves and ranks papers for clinical interests, such as psychotherapy for treatment-resistant depression. This evaluation compares a cross-encoder and an LLM relevance scorer on the same candidate papers, then examines two ways to combine their scores.

The comparison measures ranking near the top of the list and coverage of reference-positive papers within the first fifty results. It uses existing systematic-review screening labels rather than new clinician ratings.

The tested LLM configuration had higher nDCG@10 on all three development topics. Recall@50 was higher on two topics and lower on one. Using CE scores to order papers within each LLM grade also had topic-dependent results. Restricting the candidate pool reduced the number of papers requiring LLM scoring, with losses in candidate recall on two topics.

These are descriptive results for the configurations and development pools tested. Generalization to unseen topics and usefulness to clinicians remain unmeasured.

## Evaluation scope

The product has several jobs:

**Define an interest → retrieve papers → match and rank them → generate cards → accumulate evidence.**

This experiment isolates **matching and ranking**. Given a fixed set of papers, which scoring method brings reference-positive papers closer to the top?

Holding the candidates fixed matters. If one system searches PubMed and another searches a local database, a difference in the final feed could come from the source, query, candidate selection, or ranker. It would be difficult to know what to change.

This is therefore a component comparison, not an end-to-end comparison of the old and new SciSpark products.

## The data: three clinical topics, with existing labels

The evaluation uses three topics from the CLEF Technology Assisted Reviews collection. The task starts with papers returned by a systematic review’s Boolean search and asks systems to prioritize relevant records for screening. This provides a reference for testing ranking within an existing candidate pool. [CLEF task documentation](https://github.com/CLEF-TAR/tar/tree/master/2019-TAR/Task2)

For each topic, the evaluation pool contains all abstract-stage positives in the available reference pool and 200 abstract-stage negatives selected using a fixed hash ordering. The negative selection did not use either model’s scores.

| Topic | Papers evaluated | Abstract-stage positives | Final-inclusion positives |
|---|---:|---:|---:|
| Psychotherapy for depression in people with COPD | 216 | 16 | 11 |
| Psychotherapy for treatment-resistant depression in adults | 237 | 37 | 10 |
| Antidepressants for insomnia in adults | 229 | 29 | 20 |
| **Total** | **682** | **82** | **41** |

The two label types answer different questions. Abstract-stage labels describe the review’s screening decisions. Final-inclusion labels describe eligibility after full-text assessment. Neither is a direct measurement of what an individual clinician would find useful in a feed.

These were development topics that had already been inspected. The pools also contain a higher proportion of positives than the original review search results because negatives were sampled. The results should not be presented as an official full-pool CLEF benchmark or an estimate of live-feed performance.

## Ranking configurations and metrics

**The cross-encoder:** `jina-reranker-v2-base-multilingual`, accessed through a hosted reranking API. It scores a query and a paper together. This stage did not require stored paper embeddings or a separate embedding call. [Jina model card](https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual)

**The LLM:** `gpt-4o-mini-2024-07-18`, at temperature 0, using the original clinical relevance prompt in a one-paper-per-request format. It received a structured clinical interest and returned a relevance grade from 0 to 4, matching fields, and a supporting quotation.

The rubric distinguished a close condition-and-treatment match from a partial or unrelated match. This was the clinical scorer—not the general Wiki scorer or a separate LLM evaluator. The LLM produced predictions; the existing dataset labels evaluated them.

Both arms received the same paper identities, titles, and first **1,800 characters** of each abstract. Neither inherited a psychiatry keyword filter. The ranking comparison used raw scores before downstream entry and quote-validation rules.

This controlled the submitted paper text and candidate pool. It did not isolate model architecture: the CE used a natural-language query, while the LLM used structured interests and a clinical rubric. The comparison is between these two concrete configurations.

The evaluation uses two main metrics:

- **nDCG@10:** how well reference-positive papers are placed near the top of the first ten results. Higher is better; 1 is ideal. It is not classification accuracy.
- **Recall@50:** the fraction of a topic’s reference positives found in its first fifty results. The denominator includes all positives in that topic’s evaluation pool.

The LLM’s five grades create many ties. For both models, metrics are calculated as expectations under random ordering within exact score ties. This is why some recalls represent fractional expectations.

## Experiment 1: score the same full candidate pool

The primary results use abstract-stage labels.

| Topic | CE nDCG@10 | LLM nDCG@10 | CE Recall@50 | LLM Recall@50 |
|---|---:|---:|---:|---:|
| Depression with COPD | 0.731 | **0.900** | **100.0%** | 78.8% |
| Treatment-resistant depression | 0.576 | **0.628** | 59.5% | **77.7%** |
| Insomnia | 0.687 | **0.730** | 69.0% | **94.9%** |

The LLM had higher nDCG@10 on all three topics. On the COPD topic, its Recall@50 was lower: 78.8%, compared with 100.0% for the CE. The two metrics therefore give different comparisons on this topic.

The metrics describe different aspects of the list: nDCG@10 measures placement near the top, while Recall@50 measures coverage at a larger cutoff. Their relative importance depends on the intended reading or screening task.

Results also depend on the reference label. On treatment-resistant depression, LLM nDCG@10 was **0.628** against abstract-stage labels and **0.209** against final-inclusion labels. These endpoints reflect different screening decisions; the models received a truncated abstract for both evaluations.

The complete secondary table is in the [methods and evidence appendix](blog-ce-vs-llm-clinical-feed-methods.md).

## Experiment 2: use the CE to break LLM ties

The LLM assigned its highest grade to 43 papers in the treatment-resistant depression topic and 37 in insomnia. A five-level rubric could identify a useful group without ordering that group well.

The first combination sorts by LLM grade, then by CE score within each grade. Every paper remains eligible. These exploratory combinations reuse saved scores and do not require new model calls.

| Topic | LLM nDCG@10 | LLM + CE tie-break nDCG@10 |
|---|---:|---:|
| Depression with COPD | **0.900** | 0.861 |
| Treatment-resistant depression | 0.628 | **0.783** |
| Insomnia | 0.730 | **0.845** |

The combination increased nDCG@10 on two topics and decreased it on one. No held-out evaluation of this combination was performed.

It also has a clear limitation: a tie-break cannot rescue a paper assigned to the wrong grade. A high CE score cannot move a grade-0 paper ahead of a grade-4 paper under this rule.

## Experiment 3: CE candidate selection before LLM ranking

Another possible design is to run the CE first, keep its top fifty or hundred papers, and ask the LLM to score only those candidates.

This combination was simulated using the existing pointwise outputs. Reusing them is possible because each LLM request contained one paper and did not depend on the surrounding candidate list.

The first check was how many positives survived the CE cutoff:

| Topic | Positives retained in CE top 50 | Positives retained in CE top 100 |
|---|---:|---:|
| Depression with COPD | 16/16 — 100.0% | 16/16 — 100.0% |
| Treatment-resistant depression | 22/37 — 59.5% | 33/37 — 89.2% |
| Insomnia | 20/29 — 69.0% | 25/29 — 86.2% |

Across these pools, the number of topic–paper records needing LLM decisions would fall from 682 to 150 with a top-50 cutoff, or to 300 with a top-100 cutoff. These are potential decision counts, not measured latency or dollar savings.

But the cutoff creates an upper limit on downstream recall. No reranker can recover a paper that it never receives.

Treatment-resistant depression makes this concrete. Full-pool LLM scoring with CE tie-breaking achieved **0.783 nDCG@10 and 81.1% Recall@50**. Restricting that same combination to the CE’s top fifty preserved **0.783 nDCG@10**, while Recall@50 fell to **59.5%**.

In this example, nDCG@10 was unchanged while Recall@50 decreased by 21.6 percentage points. Both metrics are needed to describe the effect of candidate selection.

## Separate diagnostic: quote validation

The clinical scorer also returns quotations. The downstream quote gate was checked separately from ranking.

Of the 82 abstract-stage positives, 77 passed the raw entry decision and 72 remained after the lexical quote validator. The quote gate therefore removed five additional reference positives.

This does not show that quote validation is unnecessary. It shows that a validation rule can change which papers reach the user and needs its own evaluation. A quotation matching source text also does not establish that it supports the model’s conclusion. Semantic support and summary accuracy were not measured here.

## Limitations and further evaluation

The comparison covers one CE configuration and one clinical LLM configuration on three previously inspected topics, with sampled negatives and one output per paper. Query representation and instructions differ between the two configurations. The results do not isolate model architecture or establish a general ranking advantage.

A further ranking evaluation could freeze the configurations, use unseen topics, and include repeated model calls to measure output variation. Topics beyond treatment efficacy, including safety, would broaden the scope. The CE, LLM, and combined configurations would need to be compared under the same evaluation conditions.

Retrieval requires a separate evaluation because this comparison starts with fixed candidate pools. On a frozen corpus, retrieval methods could be compared using the same query information and candidate budget. For live PubMed retrieval, saving queries, dates, filters, and returned PMIDs would allow measurement of recovery against independently assembled eligible papers. That would measure recovery of known positives, not completeness of all relevant literature.

Whether the final feed helps clinicians track evidence is a separate user-evaluation question. Neither the screening labels nor the ranking metrics measure that outcome here.

Within these development pools, the LLM had higher nDCG@10 on all three topics, while Recall@50 and the effect of CE tie-breaking varied by topic. CE candidate cutoffs reduced prospective LLM scoring volume and limited downstream recall. These observations define the measured tradeoffs; the preferred configuration remains dependent on the task and further evaluation.

---

*Evidence: all three experiments above are completed analyses of saved outputs. The combinations are exploratory offline replays. Exact settings, secondary results, scripts, and local evidence links are collected in the [methods appendix](blog-ce-vs-llm-clinical-feed-methods.md). No new paid experiment was run to prepare this article.*
