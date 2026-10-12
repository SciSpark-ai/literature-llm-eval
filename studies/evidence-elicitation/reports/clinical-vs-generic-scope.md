# Generic ranking versus the clinical pipeline

## Correction to the interpretation of the TREC experiments

The score-only LLM in `scripts/automatic_followup.py` is an experimental generic relevance grader. It does **not** invoke Psychiatry's `clinical-stage-a` skill, clinical query planner, study-design gates, match-layer selection or evidence extraction. Accordingly, the CE/LLM comparison cannot establish which complete product pipeline is better.

Missing PICO annotations do not imply that a paper contains no population/intervention/comparator/outcome information. However, TREC document-relevance labels cannot certify extraction or clinical matching of those fields.

Current clinical `grade/stage-a.ts` consumes clinician watch entries and candidate titles/abstracts. Watch entries carry condition, optional second condition, treatment, population and outcome. The prompt assigns graded matches (including partial matches), checks condition/treatment separately, and requires source quotations. It does not require pre-existing PICO fields on every paper or enforce four-field exact equality. The stage-A watch payload does not include a comparator. Comparator extraction in later evidence/digest code is a separate capability; do not conflate those stages.

## PubMed comparison: separate questions

The current local PubMed adapter explicitly requests `sort=pub_date`, including clinical enumeration. Thus the current clinical feed is not simply PubMed Best Match. PubMed includes query translation/Automatic Term Mapping, MeSH indexing, fielded search and its own ranking. These are not reproduced by local BM25. Sources: [PubMed help](https://pubmed.ncbi.nlm.nih.gov/help/), [Best Match paper](https://pubmed.ncbi.nlm.nih.gov/30153250/).

### A. Controlled local retrieval (implemented in retrieval-v3)

Hold corpus, topic text, label version and output depth fixed. Compare BM25, exact vector, PostgreSQL full-text ranking and specified RRF hybrids. Keep the original corpus unchanged while testing cleaner repairs separately. This isolates choices within the local benchmark but does not reproduce PubMed.

### B. Clinical PubMed query planning (next protocol, not yet run)

Use a frozen psychiatric topic list and existing systematic-review inclusion lists where suitable. Compare:

1. Plain condition/treatment query.
2. The actual deterministic clinical MeSH/synonym query builder.
3. Deterministic queries plus the actual LLM planner's extra queries.

Use identical PubMed date windows, metadata filters, request limits and enumeration policy. Save query strings, translated queries, timestamps, returned PMIDs and fetched metadata. Evaluate known included-study coverage, candidate volume, unique additions, duplicates and API/runtime cost. Coverage of a review's included studies is not whole-PubMed recall; papers outside inclusion lists are not automatically irrelevant. Verify each review's eligibility, date scope and identifier mappings before scoring.

### C. Ranking after PubMed retrieval

Freeze a common fetched candidate pool and identical visible text. Compare PubMed order (specify Best Match or date order), CE, generic LLM relevance, and the actual clinical grader/selector as separately named arms. PubMed's order is a distinct baseline from SciSpark's query enumeration. Evaluate only metrics supported by existing labels; graded psychiatric relevance and card faithfulness may remain pending until final human review.

### D. End-to-end product comparison

Compare local retrieval and PubMed workflows only as complete systems. Report corpus overlap and source coverage separately from rank quality. Live PubMed cannot be inserted into historical CORD-19/TREC results without a justified identifier mapping and compatible corpus/label protocol; otherwise unjudged newer papers distort the interpretation.

## Remaining stages

Proceed with existing-label clinical field/evidence evaluation and judge validation after retrieval controls. These are planned, not completed by the generic TREC run. New psychiatric human labeling remains last.
