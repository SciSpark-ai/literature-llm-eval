<div align="center">

# literature-llm-eval

**Evaluating the performance of large language models (LLMs) in a clinical literature recommender.**

[![Site](https://img.shields.io/badge/site-read%20the%20studies-f97316)](https://scispark-ai.github.io/literature-llm-eval/) [![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE) ![Studies: 2 completed, 1 planned](https://img.shields.io/badge/studies-2%20completed%20%C2%B7%201%20planned-0d9488)

**[Read the studies](https://scispark-ai.github.io/literature-llm-eval/)** · [Study 1: relevance and evidence](https://scispark-ai.github.io/literature-llm-eval/attributed-relevance-judgments/) · [Study 2: ranking](https://scispark-ai.github.io/literature-llm-eval/clinical-feed-ranking/) · [Reproduce](#reproduce)

</div>

## Why we evaluate

We built the LLM-powered [SciSpark](https://github.com/SciSpark-ai) and [SciSpark Psychiatry](https://github.com/SciSpark-ai/scispark-psychiatry) to recommend personalized research papers to scientists and psychiatry clinicians. But do LLMs perform well in this recommendation task? For example, how do they compare with cross-encoders? How stable are their outputs, and to what extent is LLM relevance scoring affected by evidence attribution? How well do LLM-written TL;DRs agree with human experts, and do they overclaim or underclaim scientific findings? Examining these questions is key to understanding the validity and limitations of LLMs in a literature recommendation system, and to guiding the improvement of its design.

Here, we address these questions in a series of studies that apply the [SciSpark Psychiatry](https://github.com/SciSpark-ai/scispark-psychiatry) pipeline to public screening data from the CLEF 2019 Technology-Assisted Review collection: three Cochrane systematic reviews, on psychotherapy for depression with COPD, psychotherapy for treatment-resistant depression, and antidepressants for insomnia. We designed the studies to evaluate the LLM at different stages of our pipeline: from scoring a paper's relevance to the user's research interest based on its abstract, to ranking the papers, to summarizing each paper's main findings (planned).

## What we found so far

1. **LLM relevance scores are unstable.** During relevance scoring, sending the identical request again at temperature zero changed the relevance score of 18% of papers, and the keep-or-drop decision for 11%.
2. **The quote check, not the judgment, loses relevant papers.** Asking the LLM to quote its evidence in the same call as scoring did not clearly change the scores beyond this run-to-run variation, but it lost relevant papers at the quote check: of the 62 relevant papers the LLM kept, 34 (55%) came with a quote that could not be found word for word in the abstract, so the pipeline would have dropped them. Splitting scoring and evidence attribution into two separate calls recovered these papers: 96–100% of the kept relevant papers came with evidence found word for word in the abstract, at about 1.65 times the tokens.
3. **The LLM ranks well, but cut-offs before it lose papers.** When its scores were used for ranking, the LLM placed relevant papers nearer the top than a cross-encoder on all three topics (nDCG@10 of 0.63–0.90 against 0.58–0.73), and found more of the relevant papers in its first 50 results on two of the three (Recall@50 of 78–95% against 60–100%). Using the cross-encoder to cut the candidate pool before the LLM saved 78% of LLM calls but dropped up to 15 of 37 relevant papers.

> **Takeaway.** Together, our studies reveal an advantage of LLMs in ranking precision, but limitations in stability and in recall wherever a check or a cut-off sits between the LLM and the reader. They suggest two designs that may improve LLM performance in a literature recommendation system: separating relevance scoring from evidence attribution, and measuring what every filtering step removes.

## Studies

| Study | Pipeline stage | Question | Read |
| --- | --- | --- | --- |
| [Attributed relevance judgments](studies/attributed-relevance-judgments/) | Relevance scoring and evidence attribution | How stable are LLM relevance scores, and does asking the LLM to quote its evidence change them or lose relevant papers? | [Web page](https://scispark-ai.github.io/literature-llm-eval/attributed-relevance-judgments/) · [Report](studies/attributed-relevance-judgments/REPORT.md) |
| [Clinical feed ranking](studies/clinical-feed-ranking/) | Ranking | How does an LLM compare with a cross-encoder for ranking a clinical feed, and can the two be combined? | [Web page](https://scispark-ai.github.io/literature-llm-eval/clinical-feed-ranking/) · [Write-up](studies/clinical-feed-ranking/reports/blog-ce-vs-llm-clinical-feed.md) |
| LLM summaries | Summarization | How well do LLM-written TL;DRs agree with human experts, and do they overclaim or underclaim findings? | Planned |

Both completed studies use three topics from CLEF 2019 Technology-Assisted Review that were also used during development, and one model configuration each. The results describe these settings; they are not general benchmarks.

## Repository layout

Each study is a self-contained folder under `studies/` and is added only once frozen: requests, responses and analysis fixed, numbers regenerable, limitations written.

| File | What it holds |
| --- | --- |
| `README.md` | The question, setup, results and how to reproduce |
| `RESEARCH_PLAN.md` or `PROTOCOL.md` | What was planned, with pass bars written before the runs |
| `REPORT.md` or `reports/` | Full results and limitations |
| `runs/`, `results/`, `data/` | Frozen outputs, generated analyses, labels and input metadata |
| `scripts/` | Analysis code and tests |

## Reproduce

No API key is needed to recompute the published numbers. Each study's README has the commands: [attributed relevance judgments](studies/attributed-relevance-judgments/README.md#reproduce), [clinical feed ranking](studies/clinical-feed-ranking/README.md#reproduce-the-saved-score-analysis).

## Data and license

Paper abstracts are not redistributed; the attributed-relevance study includes a script to refetch them from PubMed. Relevance labels come from CLEF 2019 Technology-Assisted Review and keep their own licence and attribution. Code: MIT (`LICENSE`).
