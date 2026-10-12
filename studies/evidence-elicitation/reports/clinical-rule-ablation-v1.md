# Clinical domain-filter ablation v1

This diagnostic follows `clinical-rule-retention-v1.md`. It uses the same frozen 112 records and three watches. Product source is unchanged. Production parsing, cleaning, domain matching and standard design gating execute offline; experimental variants substitute metadata fields or pack text words only. The reproduced baseline matches every previously recorded per-paper decision; the runner aborts on decision drift.

| Variant | COPD depression: abstract-positive retained /16 | Resistant depression: retained /37 | Insomnia: retained /29 | Insomnia: full-text-positive retained /20 |
|---|---:|---:|---:|---:|
| Baseline |16|37|22|15|
| All original MeSH headings |16|37|26|18|
| Existing condition names and synonyms added to domain text words |16|37|27|19|
| Both |16|37|27|19|

The existing taxonomy supplies all condition names/synonyms; no terms are mined from benchmark labels or missed titles. However, this experiment was motivated by observed failures in these topics and is a development-set analysis, not independent validation. The all-MeSH variant preserves every original descriptor from the frozen XML, rather than the production parser's five-heading limit.

Among ten abstract-negative controls per topic, retained counts are 10, 7 and 8 for every variant. This small selected control sample does not establish unchanged precision or specificity. A systematic-review exclusion is not a general clinical-feed irrelevance label.

Two insomnia abstract-positive papers still fail domain filtering in the combined variant:
- PMID 23650468: “Sentra PM (a Medical Food) and Trazodone in the Management of Sleep Disorders.” Full-text inclusion label is also positive.
- PMID 530374: “One gram of L-tryptophan fails to alter the time taken to fall asleep.” Full-text inclusion label is negative.

## Interpretation
Both metadata truncation and incomplete coverage of supported conditions contribute to candidate loss. Conditions-only expansion recovers five of seven missed abstract-positive papers, including four of five missed full-text-positive papers. The combined variant has no additional benefit over condition expansion on these records; this does not establish redundancy on other data.

Do not add bespoke phrases until this sample reaches 100%. Broader treatment-aware domain admission or watch-aware admission should be specified as a general rule and evaluated separately, including its additional candidate load. Missing MeSH data should be addressed independently of UI display limits.

## Next stage
Run actual clinical Stage A on frozen candidate sets and distinguish model topic judgement, evidence-quote validation, and deterministic match verification. Preserve rule-stage exclusions in the denominator. Comparing LLM models or rankers before separating these failures would conflate model performance with candidate availability.

No LLM has been run in this experiment; no paid API requests were made. No product files were changed.

## Artifacts and reproduction
- `runs/clinical-v1/rule-ablation.json`: per-paper outcomes and source hashes.
- `runs/clinical-v1/all-mesh.json`: original descriptors extracted with Python ElementTree from the frozen PubMed XML.
- Run `node research/study/scripts/clinical_rule_ablation.mjs` from the workspace root. It requires the frozen metadata, baseline and all-MeSH artifacts.
