# Clinical rule retention probe v1

## Question and scope
Do the production psychiatry domain filter and standard study-design gate retain papers marked eligible in existing CLEF-TAR reference labels?

This is an offline screening probe, not retrieval, ranking, LLM grading, or end-to-end feed evaluation. The production PubMed parser reads a frozen current PubMed XML snapshot through an offline transport override. No live search is evaluated. Production cleaning, domain filtering and design gating run unchanged. Source hashes are recorded in `runs/clinical-v1/rule-results.json`.

## Sample
All 82 abstract-positive topic–paper pairs in three selected reference topics, plus 10 deterministic hash-selected abstract-negative controls per topic: 112 unique papers. No reference labels are provided to the filters. All requested records were returned and parsed. Current metadata may differ from the original benchmark snapshot. This positive-enriched sample cannot estimate feed precision or real-world prevalence. Review exclusion is not necessarily irrelevance to a clinical feed.

## Results
| Review topic | Abstract-positive input | After domain filter | After standard design gate |
|---|---:|---:|---:|
| Psychological therapies for depression in COPD |16|16|16|
| Psychological therapies for treatment-resistant depression |37|37|37|
| Antidepressants for insomnia |29|22|22|

The domain filter excludes 7/29 insomnia abstract-positive records. Five of these also have positive full-text inclusion labels. The design gate adds no positive exclusions in this sample. These results establish a failure mode, not general clinical accuracy.

## Diagnosed mechanism
The domain filter tests retained MeSH headings and a separate text-word list. That text-word list lacks insomnia and sleep terms even though insomnia is present in the taxonomy. The PubMed parser retains at most five MeSH headings, prioritizing major headings, so later headings may be unavailable to downstream filtering.

Concrete example: PMID 21966075 has “chronic primary insomnia” in its title and “Sleep Initiation and Maintenance Disorders” in its original PubMed MeSH list. None of its headings are marked major; the parser retains the first five, omitting the sleep heading. The separate text-word list does not rescue its title. It is excluded as `not-psychiatric` before any LLM assessment.

The complete seven excluded IDs are 21966075, 22197474, 21798674, 23650468, 530374, 16943177 and 19192438. Per-record labels, reasons and titles are in the result JSON.

## Next experiment
Preserve this baseline. Separately compare retaining all MeSH headings and covering supported condition terms in domain text matching, then their combination. Treat changes motivated by these three topics as development-set fixes, not independent validation. After establishing candidate retention, run production Stage A and quote/match verification on the same frozen candidate inputs, with paid requests guarded by the existing $10 total budget. LLM assessment has not yet been run in this probe; no paid API calls were made for these rule results.

## Reproduction
From the workspace root: `node research/study/scripts/clinical_rules.mjs`. Public metadata preparation is in `clinical_prepare.py`; the offline rule runner makes no external requests and writes only research artifacts.
