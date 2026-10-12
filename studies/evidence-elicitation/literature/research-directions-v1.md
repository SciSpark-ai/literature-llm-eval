# Research directions arising from SciSpark: evidence-gated LLM screening

Status: reviewer draft, 2026-10-09. Development data only; no new paid calls. Companion documents: `reports/Evidence gate screening related work.md` (related-work matrix), `research_notes/Evidence gate screening related work/` (six primary-literature notes), `replay_policy_offline.py` (offline replay used in Section 2).

## 1. Provisional assessment

The candidate question in `research-protocol.md` has two halves. The first half, "how much relevant evidence is lost because quotation extraction or verification fails", is no longer open as a stand-alone finding. Two 2026 preprints already quantify verbatim-quote failure and the coverage cost of requiring a quote: Windisch et al. 2026 ("Show Your Work", oncology RCT eligibility classification, three frontier models) and "Verifiable by Construction" (arXiv 2609.15964, clinical QA, twelve models). VetScore (arXiv 2608.03675) publishes per-model exact-substring rates and shows most mismatches are formatting rather than fabrication. Our own offline replay (Section 2) shows that roughly half of SciSpark's positive quote failures are recoverable by an elision-tolerant matcher with no new model call, and the short-contiguous-span instruction removed most of the rest. A paper whose main result is "exact-match gates lose evidence" would therefore be reporting a known effect whose magnitude is largely an artifact of a strict matcher.

The second half, "does separating the relevance decision from evidence extraction improve the tradeoff", remains open in a specific form. No located work (a) runs a decide-only call and an extract-only call against a joint call under a verification gate, (b) separates the instruction effect of requiring evidence from run-to-run variance with repeated requests, (c) compares evidence-failure deferral with confidence or agreement deferral at a matched human-review budget, or (d) validates any of this at the topic level on screening data. Windisch et al. list two-call and span-offset designs as future work. This is the gap, and it is narrower than the original framing.

Most important uncertainty: whether the coupling effect (requiring evidence changes the decision itself) is larger than ordinary run-to-run variance at temperature zero, and whether it persists for stronger models. If repeated runs of the same prompt flip as many labels as the quote instruction does, the effect is noise and Direction 2 collapses. If strong models show both near-zero verbatim failure and no decision shift, the remaining contribution is confined to cheap models, which narrows the audience to cost-constrained deployments. The feasibility experiment in Section 5 is designed to answer exactly this before any further commitment.

## 2. What existing artifacts already establish (offline, no cost)

Replay of the frozen Stage A outputs (`runs/clinical-v1`, `runs/clinical-quote-v2`; 100 candidates, 75 abstract-positive, three exposed topics, GPT-4.1-mini, temperature 0). These are development data and support hypothesis generation only.

Failure taxonomy of the 34 baseline positive quote failures, classified against the visible title and abstract:

| Category | Count | Recoverable without a new call |
|---|---:|---|
| Elided fragments, all present in source, in order | 11 | yes, elision-tolerant matcher |
| Elided fragments, all present, out of order | 2 | arguably |
| Near-verbatim with minor edits (normalization) | 2 | yes, normalized matcher |
| Elided with at least one paraphrased fragment | 16 | no |
| Partial paraphrase, no ellipsis | 3 | no |

So 13 to 15 of 34 failures are matcher artifacts, not extraction failures. The contiguous-span variant left 7 positive quote failures, of which 3 are in-order elisions. Lexical validity under a tiered matcher is therefore the correct baseline; a strict substring gate overstates the loss.

Fixed-output policy replay on identical outputs (abstract-positive recall; sampled negatives are 10 per topic and not at realistic prevalence):

| Run, topic | Pos / neg | A: ignore quote | B: hard gate | Review queue under C (pos / neg) |
|---|---|---|---|---|
| v1, CD012347 | 16 / 10 | 16 / 6 | 4 / 2 | 12 / 4 |
| v1, CD010558 | 37 / 7 | 24 / 3 | 15 / 0 | 9 / 3 |
| v1, CD010753 | 22 / 8 | 22 / 1 | 6 / 0 | 16 / 1 |
| v2, CD012347 | 16 / 10 | 16 / 5 | 13 / 2 | 3 / 3 |
| v2, CD010558 | 37 / 7 | 19 / 0 | 13 / 0 | 6 / 0 |
| v2, CD010753 | 22 / 8 | 22 / 3 | 21 / 1 | 1 / 2 |

Two observations matter for design. First, the gate removes positives and negatives alike, so the review queue is positive-rich only because the pool is positive-enriched; at CLEF prevalence (1.5 to 3.4 percent positive) the same per-record failure rates would fill the queue with negatives. The workload question cannot be answered on this pool. Second, the joint prompt contains the rule "if you cannot quote support for a grade above 0, give 0", so the model self-gates: the 13 (v1) and 18 (v2) CD010558 positives with model grade 0 cannot be separated into semantic misses and quote-driven abstentions without a decide-only arm. The current protocol's RQ1 is therefore not identifiable from joint outputs alone.

Paired instruction effect (v1 versus v2, same candidates): model grade changed for 29 of 100 records, with 19 positives downgraded and 2 upgraded. Seven positives went from a nonzero grade with an exactly verified quote in v1 to grade 0 in v2, including two grade-4 records. The quote-format instruction changed relevance decisions, but with one run per condition this cannot be distinguished from run variance. This is the observation Direction 2 is built on.

## 3. Three candidate directions

### Direction 1. Characterize verification-induced loss under tiered matchers and support grading

Research question. Across screening topics and models, how much abstract-level recall does an evidence gate remove after lexical failures are separated into matcher artifacts, extraction failures, and valid-but-nonsupporting quotes?

Why it matters beyond SciSpark. Every grounded-screening product must choose a matcher and a gate; the literature reports only strict substring rates (Windisch, VetScore) or QA funnels (Verifiable by Construction). A screening-specific funnel with per-class recall would be a reusable reference.

Closest prior work and gap. Windisch et al. 2026 (coverage drop 2 to 6 points, 48 to 79 percent semantic support among valid quotes, no per-class recall, no gate on positives); Verifiable by Construction (three-tier matcher, support grading 0/0.5/1, QA not screening); VetScore (ellipsis-tolerant matching closes most of the gap); GRACE tiers. Gap: no per-class recall under a gate on screening labels, no study of instruction effects on exact-match rates, no topic-level validation.

Contribution type. Empirical characterization plus an evaluation convention (tiered matcher, failure taxonomy, support grading).

Falsifiable hypotheses. H1a: after a normalized and elision-tolerant matcher, residual positive recall loss from the gate is below 3 points on most topics for GPT-4.1-class models. H1b: residual loss is concentrated in a minority of topics with long or structured abstracts.

Minimal controlled experiment. Replay existing outputs under three matcher tiers (done for three topics); extend to expanded pools with realistic negatives for the same three topics using one joint prompt.

Datasets and labels. CLEF TAR 2019 intervention topics, abstract-level qrels primary, content-level secondary. Roughly 40 intervention topics exist in the pinned revision; 3 are exposed.

Essential baselines. Strict substring gate; normalized gate; elided gate; no gate.

Primary outcome and unit. Topic-level paired difference in abstract-positive recall between gate tiers; unit is the topic.

Confounds and failure modes. Truncation at 1800 characters; metadata absence; the self-gating rule in the prompt; model nondeterminism.

Human annotation. Semantic support grading on a stratified sample of valid quotes (two annotators, blinded to method), to separate lexical validity from support.

Feasibility. Replay is free. The expanded-pool extension for three topics fits inside the remaining budget. Topic-level validation needs new label-aligned pools and roughly 20 topics.

Stop or pivot rule. If H1a holds (residual loss below 3 points on most topics), this direction is an engineering note, not a paper, and should be folded into Direction 2 as a preliminary.

Assessment. Likely to confirm the known result. Low novelty after Windisch and Verifiable by Construction. Keep as a section, not a paper.

### Direction 2. Does eliciting evidence change the decision, and does decoupling recover it at matched cost?

Research question. When an LLM relevance decision and a verbatim evidence span are requested in one call, how much of the observed label shift is caused by the evidence requirement rather than by run variance, and does a two-stage design (decide-only call, then extract-only call or span selection) preserve decision recall while supplying verifiable evidence at matched token cost?

Why it matters beyond SciSpark. Joint decision-plus-evidence prompts are the default in grounded classification, screening tools, RAG judges, and LLM-as-judge pipelines. If the evidence requirement perturbs the decision, every such system is trading accuracy for auditability without measuring it. The classical select-then-predict literature (Lei 2016, FRESH 2020) measured this cost for trained models; no LLM-era paired measurement with two calls exists.

Closest prior work and gap. Windisch et al. 2026: label-only versus label-plus-quote in one call, three models, 200 abstracts, majority vote across runs; macro-F1 fell significantly for one model; two-call and span-offset designs named as future work. Camburu 2018 and Wiegreffe 2021: joint rationalization costs 0 to 6 points in fine-tuned models. Tam 2024, Format Tax 2026, dottxt rebuttal: format-induced loss is mostly from instruction and schema order, recoverable by reason-then-format. Lu et al. 2025 and Reasoning's Razor 2025: reasoning rerankers lose to direct rerankers and polarize confidence. Cohen 2025: decomposed calls cost roughly 2 to 3 times tokens. Gap: no paired, repeated-run isolation of the evidence-requirement effect from variance; no decide-then-extract LLM comparison under a verification gate; no cost-matched comparison; no screening topic-level validation.

Contribution type. Empirical finding with a cost-matched method comparison. A positive result yields a design recommendation (decouple, then select spans); a negative result (decoupling does not help, or the effect is noise) is also informative because the paired design isolates the mechanism.

Falsifiable hypotheses. H2a: the paired label-flip rate between decide-only and joint prompts exceeds the flip rate between repeated runs of the same prompt by at least a factor of two. H2b: decoupled decide-then-extract matches decide-only recall within 2 points while producing verified evidence for at least 90 percent of admitted positives under an elision-tolerant matcher. H2c: span selection by sentence index has higher lexical validity than free-text quoting but no higher semantic support. H2d: the recall gain from decoupling survives when evaluated at matched total tokens (joint prompt allowed the same budget, for example via a second attempt).

Minimal controlled experiment. Same frozen candidates and visible text. Arms: (J) joint decision plus quote, (D) decision only, (D+E) decision only followed by extraction only for admitted items, (D+S) decision only followed by sentence-ID selection. Three repeated requests per arm on a fixed subset to estimate variance. Report flips, recall, lexical validity by matcher tier, tokens and latency.

Datasets and labels. Expanded CLEF pools for the three development topics first (682 records, frozen). Validation on 20 to 30 unseen CLEF intervention topics with abstract-level qrels, grouped by overlapping reviews. Optionally one SYNERGY intervention dataset for a non-Cochrane check.

Essential baselines. Decide-only (upper bound on recall without evidence); joint with the contiguous-span instruction (strong joint baseline, not the weak original); joint with a retry on quote failure (cost-matched joint); cross-encoder ranking as a non-LLM reference for ranking quality only.

Primary outcome and unit. Topic-level paired difference in abstract-positive recall at a fixed admitted fraction, between D+E and J, with repeated-run variance reported as the noise floor. Unit is the topic; bootstrap over topics with grouping for overlapping reviews.

Confounds and failure modes. Batching (multiple abstracts per request) interacts with instruction effects; fix batch size and predeclare one contrast. Self-gating rule must be removed from the D arm and kept in J, or both reported. Temperature-zero nondeterminism (Atil et al., Lau 2026). Model family dependence. Truncated abstracts. Positive-enriched development pools inflate flip counts among positives.

Human annotation. Semantic support on a stratified sample of admitted quotes and selected sentences, two annotators; eligibility ambiguity on decision disagreements between arms.

Feasibility. The three-topic expanded-pool version with four arms and three repeats on a 150-record subset is estimated at roughly 2 to 4 dollars on GPT-4.1-mini, inside the remaining authorization, but only after the HTTP 429 recovery policy is settled. Topic-level validation across 20 to 30 topics with two model families is a separate, priced scope.

Stop or pivot rule. Stop if H2a fails (instruction-induced flips are within run variance) or if decide-only and joint recall differ by less than 2 points on the expanded pools. Pivot to Direction 3 if decoupling preserves recall but produces many unsupported quotes.

Assessment. Best balance of novelty, identifiability and feasibility. The mechanism is already suggested by our paired data, the closest paper explicitly leaves the design open, and the experiment is cheap to pilot.

### Direction 3. Is evidence failure an informative deferral signal at a matched review budget?

Research question. Under a fixed human-review budget, does routing items whose evidence fails verification to review recover more relevant records than routing by model confidence, multi-run disagreement, or multi-model disagreement?

Why it matters beyond SciSpark. Screening tools increasingly route uncertain items to humans (Delgado-Chaves 2025, Hilkenmeier 2026, Rahgozar 2026, Singh 2026). All route on confidence or agreement. Whether a grounding failure is a better or worse signal than confidence is unknown and generalizes to citation verifiers (HALLMARK) and RAG abstention.

Closest prior work and gap. Singh 2026 (cost-sensitive conformal deferral, break-even review cost); Hilkenmeier 2026 (three-LLM disagreement to human, about 20 percent of records); Reasoning's Razor (reasoning polarizes confidence, harming low-FPR detection); Wallat 2024 (passing citations can be post-rationalized); Patil 2025 (wrong predictions cite more contradicting cues). Gap: no risk-coverage or recall-versus-review-fraction curve for "defer iff evidence fails", and no head-to-head with confidence or agreement deferral.

Contribution type. Evaluation finding and a routing policy comparison.

Falsifiable hypotheses. H3a: at the review fraction implied by evidence failures, evidence-failure routing recovers more abstract-positives than confidence-ranked routing of the same size. H3b: combining evidence failure with low confidence dominates either alone on the recall-review curve. H3c (null): evidence failure is uncorrelated with decision error after matcher normalization, so routing on it wastes review.

Minimal controlled experiment. Requires realistic prevalence; cannot be run on the 100-record pool. On expanded pools, compute recall-versus-review-fraction curves for four signals using the arms of Direction 2 (J and repeated runs supply disagreement; D supplies grade confidence; J supplies evidence failure).

Datasets and labels. As Direction 2. Negatives are review exclusions, not clinical irrelevance; report both abstract-level and content-level positives.

Essential baselines. Random deferral of equal size; confidence-ranked deferral; repeated-run disagreement; no deferral.

Primary outcome and unit. Topic-level area under the recall-versus-review-fraction curve up to 20 percent review; unit is the topic.

Confounds and failure modes. Coarse 0 to 4 grades produce ties; evidence-failure rate depends on matcher tier and instruction, so the signal is policy-dependent; review fraction must be charged at full record cost; positive-enriched pools inflate queue precision.

Human annotation. None beyond Direction 2, if deferred items are assumed correctly handled by humans; if that assumption is relaxed, a small adjudication sample.

Feasibility. Rides on Direction 2 outputs; no additional model cost. Realistic-prevalence pools are mandatory.

Stop or pivot rule. If H3c holds on the expanded pools, drop the routing claim from any paper and report it as a negative finding within Direction 2.

Assessment. Cheap and informative as a secondary analysis but weak as a lead contribution: the signal is defined by a policy choice and the answer may be "it depends on the matcher".

## 4. Comparison and recommendation

| Criterion | D1 loss characterization | D2 coupling and decoupling | D3 deferral signal |
|---|---|---|---|
| Novelty after literature review | Low: Windisch, VbC, VetScore | Moderate: explicitly open, named as future work by closest paper | Moderate: no head-to-head exists |
| Identifiable from controlled design | Yes but trivial | Yes with repeats and a decide-only arm | Yes but policy-dependent |
| Value beyond SciSpark | Reference numbers | Design rule for grounded classification | Routing guidance |
| Cost of feasibility check | Free (replay) plus small | 2 to 4 dollars estimated | Zero marginal |
| Risk of null | High (likely small after matcher) | Medium | Medium to high |

Recommendation. Pursue Direction 2 as the lead question, with Direction 1 as its preliminary (failure taxonomy and matcher tiers) and Direction 3 as a secondary, workload-matched analysis. Drop "how much evidence is lost" as the headline.

Recommended research question. When an LLM is asked for a relevance decision and verifiable evidence, does the evidence requirement change the decision beyond run-to-run variance, and does decoupling decision from extraction preserve recall at matched cost and matched human-review workload?

Contribution statement. A paired, repeated-run measurement isolating the decision-level effect of evidence elicitation in LLM screening, a cost-matched comparison of joint, decoupled and selection-based grounding under tiered verification, and a workload-charged evaluation of evidence failure as a review-routing signal, validated at the topic level on unseen systematic-review screening topics.

## 5. Experiment matrix

Essential (E) versus optional (O). Resource tier: A existing artifacts, B minimal feasibility, C full study.

| ID | Tier | Experiment | Purpose | Status |
|---|---|---|---|---|
| E1 | A | Tiered-matcher replay on frozen outputs (done above) | Separate matcher artifacts from extraction failure | done, three topics |
| E2 | A | Fixed-output policy replay A/B/C (done above) | Show hard gate removes positives and negatives alike; queue precision depends on prevalence | done, not interpretable for workload |
| E3 | B | Decide-only arm on the frozen 100 candidates, one run | First estimate of self-gating share among grade-0 positives | not run, about 0.03 dollars |
| E4 | B | Three repeated runs of J and D on a 150-record subset of expanded pools | Noise floor for flips; tests H2a | not run |
| E5 | B | D+E and D+S arms on expanded pools, one run | Tests H2b, H2c; produces evidence-failure and confidence signals for D3 | not run |
| E6 | B | Recall-versus-review curves from E4 and E5 outputs | Tests H3a to H3c on realistic prevalence | offline after E5 |
| E7 | C | Unseen-topic validation, 20 to 30 CLEF intervention topics, grouped bootstrap | Topic-level inference | needs priced scope |
| E8 | C | Second model family on a fixed subset | Model dependence of coupling effect | optional until E4 is positive |
| O1 | C | Batch-size contrast | Interaction with instruction effect | optional |
| O2 | C | Semantic-support annotation, two annotators, about 200 quotes | Validate lexical validity against support | required before publication, optional for feasibility |
| O3 | C | Cross-encoder on expanded pools | Ranking context only | optional; HTTP 429 recovery first |

Order: E3, then E4, then E5 and E6. Do not start E7 before the go/no-go below.

## 6. Go/no-go criteria before a full study

Go if all hold on the expanded development pools:
1. Instruction-induced paired flip rate between J and D exceeds twice the repeated-run flip rate of either arm alone (H2a).
2. Decide-only recall exceeds joint recall by at least 3 points on at least two of three topics after an elision-tolerant matcher, so the effect is not a matcher artifact.
3. Decoupled D+E or D+S recovers at least half of that gap at no more than 2.5 times the joint token cost.
4. The closest-work matrix still leaves the two-call, repeated-run, workload-charged design unclaimed after forward-citation chasing of Windisch et al. 2026.
5. Abstract-level labels and protocol objectives are usable for at least 20 unseen intervention topics with overlap grouping documented.

No-go if 1 or 2 fails: write an engineering note on matcher tiers and the short-span instruction and stop. Partial go if 3 fails: report the coupling effect as a finding without a method claim.

## 7. Publication categories

Contingent on the eventual contribution; none is promised.
- Empirical finding with method comparison (if H2a and H2b hold): information-retrieval or NLP evaluation venues that accept controlled empirical studies, or a health-informatics methods journal that publishes screening-automation evaluations.
- Negative or characterization result (if only Direction 1 survives): a short paper or a methods note in a systematic-review methodology journal, framed as evaluation conventions for grounded screening.
- Evaluation-framework contribution (if the tiered matcher, failure taxonomy and workload-charged curves are the main value): an evaluation-track or resource-track submission with released harness and frozen manifests.

## 8. Limitations of this assessment

Three exposed topics, one model, one run per condition; sampled negatives at non-realistic prevalence; CLEF exclusion labels are not clinical irrelevance; the joint prompt's self-gating rule confounds RQ1; the literature search did not include forward-citation chasing of Windisch et al. 2026 or GitHub README audits of screening tools; several full texts were unreadable (publisher 403) and are marked in the notes. The novelty claim is "not found", not "does not exist".

## 9. Post-draft verification (2026-10-09)

The item flagged in the matrix as the most likely hidden precedent (Information 17(5):501, earlier misattributed to Galli et al.) is Nawrath et al. 2026. Its full text asks for a verdict, a free-text explanation and a confidence rating only; no quotation requirement, no verification, no gate, no review routing. The gap statement for Direction 2 is unchanged. Forward-citation chasing of Windisch et al. 2026 remains undone.

E3 decision: recommended as the first paid step, pending explicit authorization. It needs a decide-only prompt variant that removes the quote field and the "if you cannot quote support, give 0" rule, and nothing else. Seven OpenAI batches on the frozen 100 candidates; the HTTP 429 recovery policy concerned the cross-encoder provider and is not a prerequisite for E3.

## 10. E3 outcome (2026-10-09, after authorization)

Report: `reports/clinical-decide-only-v1.md`. Decide-only recovers 10 of 13 joint-zero positives on CD010558 (34 versus 24 above grade 0) and nothing on the other two topics, so go/no-go criterion 2 is not met at the grade-above-0 cut. More important, removing the quote rule reshaped the grade scale: grade 3 vanished and 15 positives dropped from 3 or 4 to 1, so at grade 2 or higher decide-only retains fewer positives than the joint prompt on all three topics. Consequences for Direction 2: (a) compare arms at matched admitted fraction and across thresholds, never at one grade cut; (b) the decoupled design must include a calibration step or a rank-based endpoint; (c) E4 repeats are now the gating experiment, because decide-only versus joint flipped 29 of 100 grades, the same count as joint versus quote-variant. Direction 7 (noise floor) rises in priority accordingly.

## 11. Pointer

The related-work matrix (30 rows, verification depth per row), explicit novelty uncertainties, and reusable methodological standards are in `reports/Evidence gate screening related work.md`. Its verdict matches Section 1: components are known individually; the hard-gate positive-class recall loss on screening labels, the joint-versus-two-call comparison, evidence-failure routing with charged workload, and topic-level validation are the untested composition.

## 12. E4/E5 outcome (2026-10-09)

Report: `reports/e4-e5-v1.md`. H-A1 is not supported: the within-prompt raw flip rate is 0.182 and the flip rate at grade at least 1 is 0.108, about twice the stated bounds. H-B1 is not supported: the between-prompt flip rate is 0.306, 1.69 times the within-prompt rate, although the topic-level difference is positive on all three topics (0.117 [0.067, 0.159]). H-C1 is supported: decide-then-extract verifies 69 of 72 admitted positives, all at the production exact tier, and sentence selection verifies 72 of 72. H-C2 is supported: decide-then-extract uses 1.65 times the joint prompt's tokens. Go/no-go status: criterion 1 (coupling above twice the noise) not met; criterion 2 (decide-only recall gain at least 3 points on two of three topics after tolerant matcher) met on all three topics, using the mean over repeats: with the tolerant matcher applied to each joint run's own quotes the joint prompt keeps 20.25 of 37, 12.50 of 22 and 7.75 of 16 positives, against 32.00, 21.50 and 15.75 admitted by decide-only (before the quote gate the raw-grade gain exceeds 3 points on CD010558 only); criterion 3 (decoupling recovers at least half the gap at no more than 2.5 times cost) met (69 verified positives against 39 for the joint prompt under the tolerant matcher, at 1.65 times the tokens). The no-go rule fires on criterion 1 alone. Next: stop; write the engineering note on matcher tiers and the short-span instruction. The noise floor (Direction 7) is the result to carry into that note: one run per prompt variant cannot separate an instruction effect from run-to-run variance on this grader.
