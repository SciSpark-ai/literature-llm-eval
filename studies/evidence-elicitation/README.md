# Does asking an LLM for evidence change its answer?

A small, fully frozen measurement study of a biomedical abstract screener, with the evaluation harness used to run it. Part of the **literature-llm-eval** program (evaluating LLM behaviour at each stage of a literature-monitoring system); this is Project A, the only project frozen so far.

**Setting.** A production tool asks GPT-4.1-mini for a 0 to 4 relevance grade and a verbatim supporting quote in one call, and drops any paper whose quote cannot be found in the abstract. Relevant papers were being dropped.

**What is here.**
- The frozen requests, responses and graded results for every run behind the write-up: one joint-prompt baseline, one short-quote variant, one decide-only probe, three repeats of each of the two prompts, and three evidence-extraction arms. Abstract text has been removed (see "Data and labels"); PMIDs, titles, grades, model outputs and quoted excerpts are kept.
- Offline analysis that regenerates the numbers in `reports/e4-e5-v1.md` from those files.
- The harness: a guarded API transport (model allowlist, no silent retries, persistent response cache keyed on the request body, durable spend ledger) and the capture and replay scripts.
- A six-area primary-literature review and a 31-paper related-work matrix (`literature/`).

**Headline numbers** (three development topics, 100 abstracts, one model; descriptive, not held-out):

| Quantity | Value |
|---|---:|
| Raw grade changed between byte-identical repeated requests (temperature 0) | 18.2% |
| Keep-or-drop decision changed between identical repeats | 10.8% |
| Grades differing between joint and decide-only prompts | 30.6% (1.69× the noise; pre-stated bar was 2×, so no coupling claim) |
| Relevant papers kept with a production-valid quote, one-step prompt | 28 of 62 (45%) |
| Same, one step plus a retry call on quote failure | 55 of 62 (89%) at 1.34× tokens |
| Same, decide first then extract a quote | 69 of 72 (96%) at 1.65× tokens |
| Same, decide first then select a sentence number | 72 of 72 (100%) at 1.68× tokens |

Start with `reports/tech-report-plain-summary.md` (no background assumed), then `reports/e4-e5-v1.md` (full results and limitations).

## Reproduce the numbers

Requirements: Python 3.9 or later; `httpx` and `pytest` for the tests (`pip install httpx pytest`). No API key.

Without fetching anything, every grade-based number regenerates from the frozen files:

```bash
python3 -m pytest -q                      # harness guards, matcher tiers, analysis functions
python3 scripts/e4_analysis.py            # noise floor and prompt effect  -> runs/e4/analysis.md
python3 scripts/e5_analysis.py            # evidence policies and cost     -> runs/e5/analysis.md
python3 scripts/clinical_decide_only_compare.py
```

Two quantities compare quotes against the abstract text and therefore need the text: the joint prompt's "any tier" verification counts (`joint_gated_recall` in E4; the `J` rows in E5) and the matcher-tier taxonomy in `literature/replay_policy_offline.py`. Without the text the scripts say so and skip or fall back to the production exact verdict. To compute them locally:

```bash
python3 scripts/fetch_abstracts.py --verify   # refetch ~660 abstracts from PubMed into data/abstracts.json
python3 scripts/e4_analysis.py
python3 scripts/e5_analysis.py
python3 literature/replay_policy_offline.py
```

Refetched text is the raw PubMed abstract cut to the same 1800-character window; the model saw the output of a private cleaning step, so these text-dependent counts are labelled approximate in the output. The committed `runs/e4/analysis.json` and `runs/e5/analysis.json` hold the exact values computed before redaction; running the scripts overwrites them, and `git diff` shows the difference.

## What cannot be reproduced from this repository alone

- **Capturing or replaying through the production grader.** The `.mjs` scripts load the production grading code from a private package by relative path and check its source hashes. The frozen `stage-a-requests.json` and `stage-a-responses.json` are what those scripts produced; all analysis starts from them.
- **Making new paid calls.** The `*_paid.py` and `e5_extract.py --run` scripts need an OpenAI key in a private backend `.env` and append to `budget.jsonl`. They are included so the guard logic can be read and tested.
- **Byte-identical requests.** Request ids were computed on the unredacted requests and are kept as recorded; after redaction the request bodies no longer hash to them.

## Layout

```
reports/        run reports (one per experiment) and the plain-English summary
runs/           frozen per-run artifacts: config, rule results, requests, responses, graded results
runs/e4, e5     generated analyses (json and md); the committed copies are the exact pre-redaction values
runs/redaction-manifest.json   every removed text: hash -> PMID, kind, length
scripts/        harness (pilot_api.py, pilot_core.py, pilot.py), capture/replay (.mjs), analysis (.py),
                redact_abstracts.py and fetch_abstracts.py
tests/          pytest suite
literature/     research notes, 31-row related-work matrix, direction documents, offline replay script
data/           CLEF TAR 2019 topic and label files used (pinned revision recorded in data_manifest/)
budget.jsonl    append-only spend ledger; reservations are conservative upper bounds and never released
research-protocol.md, engineering-evaluation-roadmap.md   the original plans, kept as written
```

## Data and labels

Topics and relevance labels are from CLEF 2019 Technology-Assisted Review, Task 2, intervention reviews CD012347, CD010558 and CD010753, pinned at the revision recorded in `data_manifest/clinical-reference-audit.json`, under that project's terms. Abstract-level labels are primary; content-level labels are secondary. Review exclusion is not clinical irrelevance.

Paper abstracts are publisher-copyrighted and are not redistributed. `scripts/redact_abstracts.py` replaced every abstract (raw PubMed text, the cleaned text sent to the model, and the numbered sentences in the sentence-selection requests) with `[ABSTRACT REDACTED sha256:…]` and deleted the raw PubMed XML; `runs/redaction-manifest.json` lists all 659 PMIDs and the hash of each removed string, and `scripts/fetch_abstracts.py` refetches them through NCBI E-utilities for local use. Titles, MeSH terms, grades, model outputs and the model's quoted excerpts (median about 150 characters, longest 536) are kept.

## Limitations, in one paragraph

Three topics that were also used during development; a candidate set deliberately rich in relevant papers (75 of 100), so nothing here measures precision or review workload at realistic prevalence; one model and one prompt family; evidence checked for lexical presence, not for whether it supports the grade; no human re-annotation; repeated runs share a provider backend whose fingerprint changed between runs, so the measured noise is serving-stack variation as much as sampling. The one partial run (`e4-joint-r3`, a transport error after 3 of 7 requests) is excluded from analysis and not included here.

## Related work

`literature/reports/Evidence gate screening related work.md` lists the 31 closest papers with what each establishes, what it leaves open, and how deeply it was read. The closest are Windisch et al. 2026 ("Show Your Work"), "Verifiable by Construction" (arXiv 2609.15964) and VetScore (arXiv 2608.03675). The specific combination measured here was not found in that review; the matrix records what was and was not searched.

## License

Code: MIT (see `LICENSE`). Labels and topic files: CLEF TAR, MIT; SYNERGY index, CC0 (see `data/reference-audit/THIRD-PARTY.md`). Abstract text: not included; refetch from PubMed for research use. Prompts quoted from the product and its upstream project are Apache-2.0; see `NOTICE.md`.
