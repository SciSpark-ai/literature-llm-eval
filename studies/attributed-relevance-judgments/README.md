# Attributed Relevance Judgments by LLMs in Biomedical Literature Screening

A measurement study of a production screener that asks GPT-4.1-mini for a 0 to 4 relevance grade and a verbatim supporting quotation in one call, and drops any paper whose quotation is not found in the abstract. Three questions: how stable are the grades across identical runs, does the quotation requirement change them beyond that noise, and does extracting the evidence in a second step recover verifiable attribution at what cost.

Read in this order: this page (three minutes), `RESEARCH_PLAN.md` (what was planned and pre-stated before the runs), `REPORT.md` (every result and limitation). Terms follow the IR literature: a *relevance judgment* is a graded label for one document against one information need; *attributed* means it carries a checkable pointer into the source.

## Question, method, main results

**Setting.** 100 frozen abstracts from three Cochrane review topics (CLEF TAR 2019 intervention reviews), 75 relevant by published screening labels and 25 sampled negatives; one model, temperature 0; topics that were also used during development, so nothing is held out.

**Method.** Two prompts that differ by one rule: joint (grade plus quote, the production prompt) and decide-only (grade, quote field left empty). Each sent four times with byte-identical requests, distinguished only by an HTTP tag that defeats the response cache. Then three ways to attach evidence after the decision: ask for a verbatim excerpt in a second call (D+E), ask for a sentence number from a numbered abstract (D+S), or retry the excerpt only where the joint prompt's quote failed (J+R). Quotes verified at three tiers: the production exact rule, punctuation-normalized, and ellipsis-tolerant in-order fragments. Hypotheses and pass bars were written before the runs (`RESEARCH_PLAN.md`, Section 4).

**Results** (descriptive; three development topics):

| Quantity | Value | Pre-stated bar |
|---|---:|---|
| Raw grade changed between identical repeated requests | 18.2% | below 10%: not met |
| Keep-or-drop decision changed between identical repeats | 10.8% | below 5%: not met |
| Grades differing between joint and decide-only prompts | 30.6%, 1.69× the noise | at least 2×: not met, so no claim that the quote requirement changes judgments |
| Relevant papers kept with a production-valid quote, joint prompt | 28 of 62 (45%) | |
| Joint plus retry on failure (J+R), production-exact / any matcher tier | 53 / 55 of 62 (85% / 89%) at 1.34× tokens | |
| Same, decide then extract a quote (D+E) | 69 of 72 (96%) at 1.65× tokens | at least 90%, at most 2.5×: met |
| Same, decide then select a sentence (D+S) | 72 of 72 (100%) at 1.68× tokens | 100%: met |
| Joint-prompt quote failures that a tolerant matcher would have accepted | 11 of 34 strictly; 13 to 15 on a lenient reading | |

What it means in one paragraph: on this grader, two identical runs disagree on about 18 of 100 grades, so a single run per prompt variant cannot show a prompt effect; the joint prompt's lost recall comes from its own quote check rather than from its judgment; and fetching the evidence in a second step, or having the model point at a sentence instead of copying one, gives verifiable attribution for nearly every kept paper at a modest cost per paper and a lower cost per verified paper. A sentence that exists is not a sentence that supports the grade: validity here is lexical.

## What is in each folder

| Path | What it is | How to use it |
|---|---|---|
| `README.md`, `RESEARCH_PLAN.md`, `REPORT.md` | Overview, dated plan with pre-stated hypotheses, full results | Read in that order |
| `data/` | CLEF TAR labels and provenance for the three topics; the redaction manifest (every removed abstract: hash, PMID, kind) | Labels are read by the analysis scripts; the manifest drives `fetch_abstracts.py` |
| `runs/` | Frozen artifacts with abstract text redacted, one folder per run: requests, responses, and per-abstract graded results after production verification. 9 Stage A runs (joint baseline, short-span variant, decide-only, and six tagged repeats) and 3 extraction runs | Preserve the frozen artifacts; text-dependent analyses have the reproduction limits below |
| `scripts/` | The guarded API transport (`pilot_api.py`, `pilot_core.py`), the analysis library (`e45_lib.py`: three-tier matcher, sentence splitter, flip rates, bootstrap), the analyses (`e4_analysis.py`, `e5_analysis.py`, `matcher_taxonomy.py`, `clinical_decide_only_compare.py`), the extraction script (`e5_extract.py`), the request verifier, and the redaction and refetch scripts. `scripts/tests/` holds the pytest suite | See reproduction below |
| `results/` | Generated analyses: `e4/` noise floor and prompt effect, `e5/` evidence policies and cost, `matcher-taxonomy.json`, `quote-variant-comparison.json` | Regenerate with the commands below; `git diff` shows any change |

## Reproduce

Python 3.9 or later; `pip install httpx pytest`. No API key is needed.

```bash
python3 -m pytest -q scripts/tests
python3 scripts/e4_analysis.py                  # -> results/e4/
python3 scripts/e5_analysis.py                  # -> results/e5/
python3 scripts/clinical_decide_only_compare.py
```

Abstract text is not in this repository (see Data). Three quantities compare quotes against the abstract and need it: the joint prompt's tolerant-matcher counts in E4 (`joint_gated_recall`) and E5 (the `J` rows), and `matcher_taxonomy.py`. Without the text the scripts say so and skip or fall back to the production exact verdict; the committed `results/` hold the exact values computed before redaction. To recompute locally:

```bash
python3 scripts/fetch_abstracts.py --verify     # ~660 abstracts from NCBI into data/abstracts.json
python3 scripts/e4_analysis.py && python3 scripts/e5_analysis.py && python3 scripts/matcher_taxonomy.py
```

Refetched text is the raw PubMed abstract cut to the 1800-character window the model saw; the model actually saw the output of a private cleaning step, so these recomputed counts are labelled approximate.

Not reproducible here: capturing new requests through the production grader (private product package) and making paid calls (private key). The frozen `runs/` are what those steps produced.

## Cost

| Item | Estimated model cost (USD) |
|---|---:|
| Joint baseline, short-span variant, decide-only probe (one run each) | 0.078 |
| E4, six repeat runs | 0.165 |
| E5, three extraction arms | 0.041 |
| Total for this study | about 0.28 |

Costs at list rates from reported token usage; the ledger reserves conservative upper bounds about 15 times higher and never releases them.

## Data

Relevance labels: CLEF 2019 Technology-Assisted Review, Task 2, intervention reviews CD012347, CD010558 and CD010753, pinned at the revision recorded in `data/clef-labels-and-provenance.json`, under the CLEF TAR repository's terms. Abstract-level labels are primary; review exclusion is not clinical irrelevance.

Abstracts: publisher-copyrighted and not redistributed. `scripts/redact_abstracts.py` replaced every abstract (raw text, the cleaned text sent to the model, and the numbered sentences in the sentence-selection requests) with `[ABSTRACT REDACTED sha256:…]`; `data/redaction-manifest.json` lists the 659 PMIDs and the hash of each removed string; `scripts/fetch_abstracts.py` refetches them for local use. Titles, grades, model outputs and the model's quoted excerpts (median about 150 characters) are kept.

## Limitations

Three development topics; a candidate set rich in relevant papers (75 of 100), so precision and review workload at realistic prevalence are not measured; one model and one prompt family; evidence checked for presence, not for whether it supports the grade; no human re-annotation; the provider backend fingerprint changed between runs, so the measured noise is serving-stack variation as much as sampling; the decide-only schema still carried a `quote` field. One partial run (`e4-joint-r3`, transport error after 3 of 7 requests) is excluded and not included.

## Related work

The nine closest papers and what each leaves open are in `RESEARCH_PLAN.md`, Section 2. The closest precedents are Windisch et al. 2026 ("Show Your Work"), "Verifiable by Construction" (arXiv 2609.15964), VetScore (arXiv 2608.03675) and Saha and Mitra 2026 ("LLMs as Assessors"). The combination measured here was not found in a six-area review of primary literature; the full 31-paper matrix is available on request.

A blog post summarising this study is in preparation; this README is the reference until then.

## License

Code and reports: MIT (repository root). Reproduced product prompts: Apache-2.0. CLEF TAR labels: source MIT license. Abstracts: not included. See [NOTICE.md](NOTICE.md) and the license copies in `LICENSES/`.
