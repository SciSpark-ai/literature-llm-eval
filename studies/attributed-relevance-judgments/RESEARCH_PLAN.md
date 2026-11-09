# Research plan: Attributed Relevance Judgments by LLMs in Biomedical Literature Screening

Author: Linjing Jiang. Plan written 2026-10-09, before the repeated-run and extraction experiments (E4, E5) were run; the hypotheses and pass bars in Section 4 are as written then. Section 6 lists every deviation. Development data only; no held-out validation is claimed.

## 1. Background

SciSpark Psychiatry monitors PubMed for a clinician. Each new abstract is graded for relevance to the clinician's watch topic by a language model (GPT-4.1-mini) on a 0 to 4 scale. In the same call the model must copy a verbatim passage from the title or abstract that justifies the grade, and the system accepts the grade only if that passage is found in the text. This is an *attributed relevance judgment*: a graded label that carries a checkable pointer into its source. The attribution rule exists so a clinician can audit the model's reasons without reading every paper.

Development runs showed relevant papers being dropped by the attribution check. On three Cochrane review topics with published screening labels, 34 of 75 relevant abstracts that reached the model were rejected because their quotation failed the check.

## 2. What is already known

| Work | Establishes | Leaves open for this study |
|---|---|---|
| Thomas et al. 2024; UMBRELA (Upadhyay et al. 2024) | LLMs produce graded relevance judgments that agree with humans at the level of human-human agreement; prompt wording shifts agreement by 0.1 to 0.2 kappa | Single runs; no attribution requirement; web search, not biomedical screening |
| Windisch et al. 2026, "Show Your Work" | On 200 oncology abstracts, requiring a verbatim quote yields mechanically valid quotes in 83 to 91 percent of runs, only 48 to 79 percent of which support the label; coverage drops 2 to 6 points | No hard gate on positives; no decide-only versus joint comparison with repeats; two-call and span-selection designs named as future work |
| "Verifiable by Construction" (arXiv 2609.15964) | Three-tier matcher (exact, normalized, elided) and 0/0.5/1 support grading; the verbatim gate costs strong models little and weak models 13 to 19 points | Clinical QA, not screening; no decision-level recall |
| VetScore (arXiv 2608.03675) | Most exact-match failures are formatting or ellipsis joins, not fabrication; ellipsis-tolerant matching closes most of the gap | Veterinary text; no gate on decisions |
| Saha and Mitra 2026, "LLMs as Assessors: Right for the Right Reason?" | Relevance judged in one prompt and supporting passages extracted in a separate prompt; highlights over-select | No repeated-run instability; no joint-versus-decoupled comparison |
| Wiegreffe et al. 2021; Jain et al. 2020 (FRESH) | For trained models, producing a rationale with the label costs 0 to 9 points; faithfulness-by-construction pipelines are stable but lossy | Pre-LLM; no verification gate; no cost accounting |
| Figalová et al. 2026; Oami et al. 2025 | Nominally identical LLM screening runs disagree on about 8 percent of records; triplicates agree 96 to 99 percent | Not measured for graded judgments under an attribution requirement |
| Tam et al. 2024; "Format Tax" 2026 | Output-format constraints change predictions, largely through instruction wording and answer-before-reason schemas | Not tested for an evidence requirement |
| Hilkenmeier et al. 2026; Singh et al. 2026 | Screening pipelines route disagreements or low confidence to humans with workload counted | No one routes on attribution failure |

The combination studied here, a hard attribution gate on graded relevance judgments, repeated runs to separate instruction effects from noise, and a cost-matched comparison of joint versus decoupled attribution, was not found in a six-area review of primary literature (31-paper matrix in the private repository, available on request).

## 3. Problem

The attribution check and the relevance judgment are produced in one generation. Three things are therefore confounded in the observed loss: the model's run-to-run variation at temperature 0, the effect of the attribution requirement on the judgment itself, and the strictness of the string matcher. A single run per prompt variant cannot separate them, yet single-run comparisons are the norm in the screening literature.

## 4. Questions, hypotheses and pass bars (written 2026-10-09, before E4 and E5)

RQ-A, noise floor. For byte-identical requests at temperature 0, what fraction of per-abstract grades change between repeats, raw and at the admission threshold?
- H-A1: within-prompt raw flip rate below 10 percent; flip rate at grade at least 1 below 5 percent.

RQ-B, attribution requirement. Is the flip rate between the joint prompt (grade plus quote) and a decide-only prompt larger than the within-prompt repeat flip rate?
- H-B1: between-prompt flip rate at least twice the within-prompt rate, with the topic-level paired bootstrap interval of the difference excluding zero. If not, the differences seen in single runs are attributed to noise and no coupling claim is made.

RQ-C, decoupled attribution. When evidence is extracted in a second call after a decide-only judgment, by free verbatim quotation or by sentence selection, what fraction of admitted positives obtain verified evidence, at what token cost, compared with the joint prompt and with the joint prompt plus a retry on failure?
- H-C1: verified evidence for at least 90 percent of admitted positives under decide-then-extract; 100 percent lexical validity under sentence selection.
- H-C2: decide-then-extract at no more than 2.5 times the joint prompt's tokens.

Go/no-go for a larger study on the coupling question: proceed only if H-B1 holds, decide-only recall exceeds gated joint recall by at least 3 points on two of three topics after an elision-tolerant matcher, and decoupling recovers at least half of that gap at no more than 2.5 times cost.

## 5. Method

Data. 100 frozen candidate abstracts from three CLEF TAR 2019 intervention topics (CD012347 depression in COPD, CD010558 treatment-resistant depression, CD010753 antidepressants for insomnia): all 75 abstract-level positives plus 25 hash-selected negatives. Abstract-level screening labels are primary. These topics were used for development; nothing here is held out.

Prompts. Joint: the production prompt, grade plus verbatim quote, including its rule "if you cannot quote support for a grade above 0, give 0". Decide-only: identical except that rule is replaced by "leave the quote field empty; grade on your reading alone". Requests are asserted byte-identical within an arm; repeats differ only by an HTTP `user` tag that defeats the response cache.

E4. Four runs per prompt (one existing plus three new). Flip rates over all within-arm pairs (6 per arm) and all between-arm pairs (16); per-item disagreement with the modal grade; positives retained per run at grades at least 1 and at least 2; topic-level bootstrap of between-minus-within.

E5. Three extraction arms on the decide-only (or joint) decisions: D+E, a second call asking for one verbatim excerpt; D+S, a second call asking for a sentence number from a numbered split of the abstract; J+R, the same excerpt call applied only to the joint run's failed quotes. Evidence verified by three tiers: production exact rule, punctuation-normalized, ellipsis-tolerant in-order fragments. A missing entry counts as unverified.

Cost. Tokens and dollars per policy and per verified admitted positive. A guarded API transport with an append-only reservation ledger; no automatic retries.

## 6. Deviations from the plan

- The paid-call ceiling was raised from 10 to 20 dollars during E4 because concurrent jobs on the shared ledger consumed the reserved headroom; the reservation formula and the no-retry rule were unchanged.
- Run `e4-joint-r3` stopped after 3 of 7 requests with a transport read error. It was not retried; a fresh full repeat `e4-joint-r5` replaced it and the partial run is excluded.
- In one D+E batch and one J+R batch the model returned fewer entries than papers; omissions are recorded and counted as unverified.
- After a reviewer check, the joint run's own quotes are scored with the same three tiers as the extraction arms, and the go/no-go recall comparison uses gated joint recall (grade above 0 and quote verified) rather than pre-gate grades.
- Outcome against the bars: H-A1 not supported (0.182 raw, 0.108 at admission); H-B1 not supported (ratio 1.69); H-C1 and H-C2 supported. The coupling claim is not made; the study is reported as a measurement of instability and of decoupled attribution.

## 7. Out of scope

Realistic-prevalence pools, human annotation of quote support, a second model family, batch-composition effects, unseen-topic validation. Each is listed with a design in the private repository's direction documents.
