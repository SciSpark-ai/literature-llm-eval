# Additional research directions: second brainstorm

Status: reviewer draft, 2026-10-09. Extends `research-directions-v1.md` (D1 to D3). Sources: the six literature notes and their gap sections, the offline replay, and the E3 prompt work. No new paid calls were made in this session; E3 remains pending (see Section 6).

## 1. What the gap sections say is open

Across the six notes, the following were explicitly not found:
- No paper measures how batch composition (share of relevant neighbors) shifts an item's pointwise relevance grade; Fagerberg 2026 shows batch size alone moves sensitivity from 0.88 to 0.48 for one model.
- No IR or screening paper reports repeated-run flip rates for pointwise labels at temperature zero; prompt comparisons (Han 2025, Huotala 2024, Cao 2025) use single runs, while Figalová 2026 finds 8 percent record-level disagreement between nominally identical runs.
- No study varies the quoting instruction and measures the exact-match change on the same task; no validated fuzzy threshold exists in a paper.
- No paper reports inter-annotator agreement on "does this verbatim quote support this label" beyond one 70-pair author annotation.
- No screening paper measures human adjudication accuracy on deferred records; all assume the human is correct.
- No evaluation protocol for continuous literature monitoring (a standing watch topic over time) as opposed to one-off screening; living-review work (Homiar 2025, Fagerberg 2026) is prospective but not budget-charged per period.
- Nunnery 2026 names "workflow-induced evaluation targets" (abstract-level versus final-inclusion labels) but no one quantifies how much apparent LLM error is target mismatch rather than model error.

## 2. New candidate directions

### D4. Batch composition as a hidden variable in LLM relevance grading

Research question. For a fixed document and fixed prompt, how much does the pointwise relevance grade depend on the other documents in the same request, and is the effect larger when the prompt also demands evidence?

Why it matters beyond SciSpark. Almost every production grader and every LLM-as-judge pipeline batches items to save tokens. If grades are contrast-dependent, published agreement figures (UMBRELA, Thomas 2024) are conditional on undocumented batch composition, and screening sensitivity numbers are not transferable across prevalence levels.

Closest prior work and gap. Fagerberg 2026 (batch size only, sensitivity collapse at 200 to 400 per batch); listwise order effects (reversed order costs over 6 nDCG; batch permutation as ensemble); Hida 2026 and Khraisha 2024 batch 3 to 5 abstracts without analysis. Gap: no controlled manipulation of the relevant-neighbor proportion at fixed batch size and fixed item.

Contribution. Empirical finding and a design rule (shuffle and replicate, or grade singly above a measured effect size).

Falsifiable hypotheses. H4a: an abstract-positive item's probability of grade above zero is lower when its batch is positive-enriched than when it is diluted with negatives (contrast effect), by more than the repeated-run flip rate. H4b: the effect is larger under the joint evidence prompt than under decide-only. H4c (null): composition effects are within run variance.

Minimal controlled experiment. Take 30 fixed target items (20 positive, 10 negative) from the expanded pools. Build three batch contexts per item at fixed size 15: enriched (10 positives), neutral (3 positives), diluted (0 other positives). Randomize position. Two prompts (joint, decide-only). Three repeats of one context to get the noise floor. About 30 by 3 by 2 requests plus repeats.

Datasets and labels. Expanded CLEF pools (682 records); abstract-level labels.

Essential baselines. Single-item grading (batch size 1); repeated identical batches.

Primary outcome and unit. Per-item grade difference between enriched and diluted contexts, averaged within topic; unit is the topic for inference, the item for description.

Confounds and failure modes. Position effects; token-length differences between contexts; model nondeterminism; context length interacting with truncation.

Human annotation. None.

Feasibility. Roughly 250 requests of 15 abstracts on GPT-4.1-mini, estimated 1 to 2 dollars. Needs the expanded pool and realistic negatives, not the 100-record pool.

Stop or pivot rule. If H4c holds, record as a negative control and reuse the repeats for D7.

Assessment. Cheap, cleanly identifiable, generalizes to LLM judges. Weakness: could be seen as a robustness note unless the effect is large or interacts with the evidence requirement.

### D7. The noise floor: how many repeated runs does a prompt comparison in LLM screening need?

Research question. Given temperature-zero nondeterminism, what is the distribution of per-item label flips across repeated identical requests in LLM abstract screening, and how many repeats are needed to detect prompt effects of the size reported in the literature?

Why it matters beyond SciSpark. The screening literature compares prompts with one run each and reports differences of a few points. Figalová 2026 shows identical runs disagree on 8 percent of records. If typical prompt effects are inside the noise floor, a large part of the prompt-engineering literature is unpowered. This is a methodological contribution with direct consequences for LLM-judge validation as well.

Closest prior work and gap. Figalová 2026 (two runs), Oami 2025 (triplicates, 96 to 99 percent agreement), Syriani 2023 (ten runs, recall identical), Atil et al. (up to 15 percent accuracy variation), Lau 2026 (judge scores vary at zero temperature). Gap: no study estimates per-item flip probabilities as a function of grade margin, batch position and model, nor provides a power calculation for paired prompt comparisons.

Contribution. Methodological: a reusable variance model and sample-size guidance, plus empirical estimates on two model families.

Falsifiable hypotheses. H7a: flips concentrate on items with intermediate grades (1 to 3), so a binary threshold hides most instability. H7b: the paired flip rate between two prompts is not distinguishable from the within-prompt flip rate for at least one published prompt contrast replicated here (for example CoT versus zero-shot as in Han 2025). H7c: five repeats suffice to detect a 3-point recall difference at topic level with 20 topics.

Minimal controlled experiment. Five repeats of the joint prompt and five of decide-only on a 150-record fixed subset; estimate per-item flip probability; simulate power for paired designs. This reuses E4 and extends it by two repeats per arm.

Datasets and labels. Expanded CLEF pools; later 20 topics.

Essential baselines. Within-prompt repeats as the null; a known prompt contrast as a positive control.

Primary outcome and unit. Per-item flip probability and topic-level recall variance; unit is the item for variance estimation, the topic for recall.

Confounds and failure modes. Provider-side changes during the run window (model updates), cache reuse masquerading as repeats, batch composition (see D4).

Human annotation. None.

Feasibility. Estimated 1 to 3 dollars for the subset; the two-family extension needs more.

Stop or pivot rule. If flip rates are under 1 percent at the binary threshold for both models, the noise-floor argument is weak; reduce to a paragraph in D2.

Assessment. High methodological value, low risk, and it is the backbone that makes D2's H2a testable. Risk: reviewers may see it as "obvious"; the counter is that no one has published the numbers for screening.

### D10. Evaluating literature monitoring as a streaming task with a per-period budget

Research question. When a standing watch topic screens new publications period by period under a fixed reading budget, how do recall, time-to-surface for relevant papers, and review workload behave over time, and do static-screening metrics (WSS@95, nDCG) predict monitoring performance?

Why it matters beyond SciSpark. SciSpark, living systematic reviews, guideline surveillance (Fagerberg 2026) and alert services are monitoring tasks, yet they are evaluated with one-shot screening metrics. A streaming protocol with a per-period budget, delay metrics and drift detection would be reusable by any living-evidence program.

Closest prior work and gap. Living systematic review automation (Homiar 2025; Fagerberg 2026 prospective triage); TAR stopping rules (Cormack and Grossman; Callaghan and Müller-Hansen; Repke 2026 shows most stopping methods miss targets). Gap: no simulation protocol that replays a review's candidate pool in publication-date order with periodic budgets and measures delay, backlog and drift.

Contribution. Evaluation framework and benchmark protocol built on existing CLEF pools (publication dates are available from PubMed metadata), plus an empirical comparison of grading policies under streaming.

Falsifiable hypotheses. H10a: rankings of methods by WSS@95 on the static pool do not match rankings by mean surfacing delay under a fixed per-period budget. H10b: evidence-gated policies increase delay more than they reduce unsupported admissions when the budget is tight. H10c: a review-queue policy accumulates backlog that a static metric never charges.

Minimal controlled experiment. Replay the three expanded pools in publication-date order with quarterly periods and a budget of k items per period; compare fixed-output policies from existing outputs (no new calls) first; then one new grading run if needed.

Datasets and labels. CLEF pools with PubMed dates; abstract-level labels; later SYNERGY sets with dates.

Essential baselines. Date order (what PubMed sort=pub_date gives), static ranking by cross-encoder, LLM grade threshold, review-queue policy.

Primary outcome and unit. Mean and tail surfacing delay for relevant records at fixed budget; unit is the topic.

Confounds and failure modes. Date metadata quality; Boolean-pool construction already filters by date; drift in vocabulary across decades may not resemble a live feed.

Human annotation. None for the protocol; usefulness claims would need clinician review later.

Feasibility. The fixed-output replay is free. New grading runs reuse D2 outputs.

Stop or pivot rule. If H10a fails (static and streaming rankings agree), the protocol is a convenience, not a finding; keep it as an engineering evaluation.

Assessment. Most product-aligned and least crowded, but the contribution is a protocol rather than a mechanism, which some venues value less. Strong candidate for a resource or evaluation track.

### D5. Lexical validity versus semantic support: can facet-structured decisions be checked deterministically?

Research question. Among verified verbatim quotes, what fraction actually supports the facet-level decision (condition match, treatment match), and can a deterministic facet-coverage check on the quote approximate human support judgments well enough to replace an LLM judge for routing?

Why it matters beyond SciSpark. Windisch 2026 and Verifiable by Construction show that lexical validity overstates support (48 to 79 percent, and 37 percent strictly supported for one strong model). Everyone falls back to an LLM judge, which is itself unvalidated. Structured decisions (PICO facets) offer a cheap, auditable alternative that generalizes to eligibility screening and clinical-trial matching.

Closest prior work and gap. AIS and AttrScore (support categories), Verifiable by Construction (0/0.5/1 grading, kappa 0.85 on 70 pairs), Wallat 2024 (post-rationalized citations), Patil 2025. Gap: no deterministic support check tied to facet-structured labels, and no inter-annotator data on quote-level support for screening.

Contribution. Evaluation method plus a small annotated resource.

Falsifiable hypotheses. H5a: at least 20 percent of lexically valid quotes supporting grade 3 or 4 do not mention the treatment facet at all. H5b: a facet-coverage check agrees with human support labels at kappa above 0.6. H5c: routing on facet-coverage failure recovers more decision errors per reviewed item than routing on lexical failure.

Minimal controlled experiment. Sample 200 verified quotes stratified by grade and topic from existing outputs (free); two annotators grade support 0/0.5/1 blinded to method; compute facet-coverage automatically using the pack vocabulary; compare.

Datasets and labels. Existing outputs; new support annotations.

Essential baselines. LLM judge (frozen rubric), random.

Primary outcome and unit. Agreement with human support labels; unit is the quote, with topic-stratified reporting.

Confounds and failure modes. Vocabulary gaps in the pack inflate false "no coverage"; annotators see the grade and anchor on it; sample too small for per-topic claims.

Human annotation. Essential: two annotators, 200 quotes, adjudication.

Feasibility. Zero API cost; annotation time is the constraint.

Stop or pivot rule. If H5b fails (kappa under 0.4), the deterministic check is not viable; report the support rates alone as part of D1.

Assessment. Cheap in dollars, expensive in annotator time, and the finding risks being "LLM judge needed after all". Good as a component of a larger paper, weak alone.

### D6. How much apparent screening error is target mismatch?

Research question. Against systematic-review labels, what share of an LLM screener's false positives are records that a clinician would still want surfaced (scope exclusions, wrong design, superseded studies) and what share of false negatives are content-level exclusions invisible at the abstract stage?

Why it matters beyond SciSpark. Nunnery 2026 argues evaluation targets are workflow-induced; every screening paper computes precision against review labels and treats exclusions as irrelevance. Quantifying the mismatch changes how workload and precision numbers should be read for monitoring products.

Closest prior work and gap. Nunnery 2026 (conceptual), Dennstädt 2024 and Homiar 2025 (note the two label levels), CLEF two-level qrels. Gap: no annotated breakdown of exclusion reasons for LLM false positives, and no estimate of how much the gap changes method rankings.

Contribution. Empirical measurement and an evaluation recommendation.

Falsifiable hypotheses. H6a: more than a third of LLM false positives against abstract-level labels are review-scope exclusions a clinician rates as relevant to the watch topic. H6b: method rankings change when scope exclusions are removed from the negative set.

Minimal controlled experiment. Sample 150 LLM-positive, label-negative records across the expanded pools; one clinician and one methodologist label exclusion reason and clinical relevance to the watch; recompute precision and method rankings.

Datasets and labels. Expanded CLEF pools; new reason labels; Cochrane exclusion tables where available.

Essential baselines. Abstract-level versus content-level label comparison already in the audit.

Primary outcome and unit. Share of false positives by reason; unit is the record, stratified by topic.

Confounds and failure modes. Only psychiatry topics so far; clinician relevance is itself subjective; Cochrane exclusion reasons may be unavailable for abstract-stage exclusions.

Human annotation. Essential, including a clinician.

Feasibility. Zero API cost; annotation is the cost.

Stop or pivot rule. If H6a fails (scope exclusions under 10 percent), review labels are an adequate proxy and the point is moot.

Assessment. Important for interpreting everything else, but it is a measurement study whose value depends on the clinician's availability.

## 3. Comparison

| Direction | Novelty | Identifiability | Value beyond SciSpark | Feasibility cost | Null risk |
|---|---|---|---|---|---|
| D2 (v1 lead) coupling and decoupling | moderate | good with D7 | design rule | 2 to 4 dollars | medium |
| D4 batch composition | moderate | excellent | judges and screeners | 1 to 2 dollars | medium |
| D7 noise floor and power | moderate, methodological | excellent | all prompt-comparison papers | 1 to 3 dollars | low |
| D10 streaming monitoring protocol | moderate to high, protocol | good | living evidence programs | free replay, then shared | medium |
| D5 facet support check | moderate | needs annotation | attribution evaluation | annotation time | medium to high |
| D6 target mismatch | moderate | needs clinician | screening evaluation | annotation time | medium |

## 4. Recommendation after the second brainstorm

Keep D2 as the lead, but make D7 its methodological core: the repeated-run design is what turns "the quote instruction changed 29 labels" into a testable claim, and the variance estimates are publishable on their own if D2's effect disappears. Add D4 as a cheap, cleanly identifiable secondary experiment that shares the same expanded pools and repeats, because batch composition is a plausible alternative explanation for any prompt effect in a batched grader. Hold D10 as the product-aligned follow-on once the expanded-pool outputs exist, since its first stage is a free replay. Treat D5 and D6 as annotation-dependent components to schedule only if a clinician's time is secured.

A combined framing that a single paper could carry: "Measurement before method: run variance, batch composition and evidence elicitation as sources of label instability in LLM abstract screening, and what decoupling recovers at matched cost."

## 5. Updated essential experiment list

| ID | Tier | Experiment | Serves |
|---|---|---|---|
| E3 | B | Decide-only arm on the frozen 100 candidates (captured; paid call pending) | D2 self-gating share |
| E4 | B | Five repeats each of joint and decide-only on a 150-record expanded subset | D7, D2 H2a |
| E4b | B | Batch-composition contexts for 30 target items, 2 prompts | D4 |
| E5 | B | Decoupled D+E and D+S arms, one run | D2 H2b, H2c; D3 |
| E6 | A | Recall-versus-review curves; streaming replay by publication date | D3, D10 |
| O2 | C | 200-quote support annotation, two annotators | D5, publication gate for D2 |
| O4 | C | 150 false-positive reason annotation with a clinician | D6 |

## 6. E3 status

The decide-only prompt differs from the production system prompt in exactly one rule. Removed:

> "quote" must be copied VERBATIM from the paper's title or abstract (at least 8 characters) and must be the passage that justifies your grades. If you cannot quote support for a grade above 0, give 0.

Inserted in its place:

> "quote": leave this field as an empty string. Do not extract or copy evidence in this task; grade on your reading of the title and abstract alone.

The JSON schema, user messages, batches, model, temperature and output cap are byte-identical to the baseline run (asserted programmatically for all seven requests). The schema still contains a required `quote` string field because the production schema cannot be changed without product code; its presence is a residual priming cue and is recorded as a limitation. Dry-run cost ceiling: 0.44 dollars conservative reservation, expected actual cost about 0.03 dollars; combined reservations 5.51 dollars, inside the 6-dollar internal lane and the 10-dollar ceiling. The paid call was not executed in this session (blocked by the session's transaction policy) and must be run by the operator; scripts: `scripts/clinical_decide_only_paid.py --run`, then `node scripts/clinical_decide_only.mjs replay`, then `python3 scripts/clinical_decide_only_compare.py`.
