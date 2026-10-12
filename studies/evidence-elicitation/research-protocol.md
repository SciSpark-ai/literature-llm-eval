# Track B — Controlled research protocol

> **Audit revision (2026-10-09):** Prospective execution order and corrected interpretation are governed by [audit response](audit-response-and-revised-plan.md). Research remains a feasibility hypothesis; no new paid block should start before provenance and budget reconciliation.

Status: prospective design, not preregistered and not a novelty claim. 2026-10-09. Companion engineering roadmap is separate.

## Candidate question and contribution
When evidence-grounded LLM screening uses generated quotations as an admission gate, how much valid evidence is lost because generation/verification fails, and can separating relevance decisions from evidence extraction improve the tradeoff between recall, unsupported inclusions and review workload?

Clinical matching alone and model/prompt comparisons are not new contributions. The candidate contribution is a controlled characterization of verification-induced exclusion, plus a tested selective policy that routes evidence failures to review rather than silently converting them to irrelevance. This policy is not assumed novel or superior; establish the gap against selective prediction, abstention, grounded classification and screening literature before locking the claim.

## Related work: initial anchors, not an exhaustive review
- Wang et al., Zero-shot Generative Large Language Models for Systematic Review Screening Automation: screening, calibration and ensembles already studied. https://arxiv.org/abs/2401.06320
- Gao et al., ALCE: citation correctness/completeness and generation evaluation already studied; lexical copying is not semantic support. https://arxiv.org/abs/2305.14627
- Evaluating Prompting Strategies and Large Language Models in Systematic Literature Review Screening: Relevance and Task-Stage Classification: prompt/model interactions already studied. https://arxiv.org/abs/2510.16091

A novelty matrix must record each paper's task, labels, evidence requirements, gate policy, failure routing, cost accounting and external validation. Abstract-level discovery alone is insufficient to claim a gap. Read closest full papers and repositories before a final protocol. Stop or pivot if the proposed contribution is already established.

## Task and label alignment
Primary task: title/abstract screening prioritization within a defined review candidate pool using explicit review question/eligibility information. Primary labels: abstract-screening decisions. Full-text inclusion is a secondary endpoint; absent full-text evidence is not necessarily model error. Do not claim personalized clinician usefulness from review labels. Exclude or separately label topics lacking usable eligibility information rather than inventing criteria.

## Research questions and hypotheses
RQ1: What is the incremental relevant-document loss attributable to evidence validation when model outputs are fixed?
RQ2: Does decoupled classification and evidence extraction improve recall/workload/unsupported-inclusion tradeoffs at matched cost compared with joint generation and hard gates?
RQ3: Do effects persist across unseen review topics, model families and repeated runs, and under realistic missing/truncated metadata?

Hypotheses are falsifiable: gains may disappear when review cost and additional model tokens are counted, or may be model/topic-specific. Negative findings remain informative when the design isolates the mechanism.

## Minimal design; avoid a full factorial sweep
Core paired replay experiment: one frozen joint output per document; compare (A) relevance-only acceptance, (B) hard lexical-evidence gate, and (C) the same gate with failure routed to an explicit uncertain/review queue. All policies see identical output; a replay isolates policy effect. C must count its additional human workload, not claim free recall.

Generation experiment: original joint scoring/extraction versus separate relevance then extraction. Keep model, visible evidence, task information and decision rule fixed; count extra calls/tokens/latency. Add sentence-ID/span selection as a predeclared comparator if budget allows; source-valid spans can still fail to support a judgement. Include the contiguous-quote prompt as a strong joint baseline, not just the known weak original.

Contextual baselines: cross-encoder and Wiki rubric. They contextualize relevance quality but are not required to produce quotes unless an explicitly costed extraction module is attached. Do not penalize only one baseline for evidence generation in a pure ranking test.

Robustness: two model families if resources permit, three repeated runs on a fixed subset, and one predeclared batch-size contrast. Common maximum visible text; separately test truncation rather than confound methods. No performance-based selection of test topics or best seed.

## Data partitions and scale
All three existing clinical topics and all exposed TREC topics are development data. They cannot become pristine test data through a retrospective split. Partition future data by review/topic, group overlapping or closely related reviews, audit duplicate PMIDs and protocols. An untouched topic set must include multiple clinical areas to support beyond-psychiatry claims.

Initial planning target: 20–30 eligible unseen review topics, subject to label/protocol availability and a topic-level precision analysis. This is a scope target, not a sufficient-power guarantee. If affordable evidence only supports a smaller pilot, label it accordingly and do not claim broad generalization. The current $10 budget supports feasibility, not a promised full multi-model paper. Obtain a priced scope before further resource commitments.

## Endpoints and analysis
Primary: change in relevant-paper recall attributable to the gate, paired by topic. Jointly report review workload/coverage and unsupported accepted decisions; improvements in one must not hide deterioration in another. Secondary: recall at fixed reading budgets, nDCG, specificity at a prespecified recall target, cost and latency. Tune any thresholds only on development data, freeze before test.

Separate failure categories: semantic relevance judgement, lexical quote failure, valid-but-nonsupporting quote, deterministic match failure, source/metadata absence, truncation, provider/schema failure. Retain all failed tasks in system reporting; do not silently drop them. Quote failures are not automatically hallucinations.

Analyze paired topic differences with topic-level bootstrap intervals; use grouped resampling when reviews overlap. Predeclare primary contrasts, report effect sizes and multiplicity handling for secondary sweeps. Avoid paper-level pseudo-replication. Model consistency requires repeated requests, not cached replay.

## Human and LLM judge evaluation, last
Existing human labels support relevance first. At the end, sample from passes/failures and method disagreements using a frozen stratified design; annotate quote support and eligibility ambiguity blinded to method. Use two qualified reviewers plus disagreement resolution where feasible; report sample counts, agreement and weighting if population estimates are made. If only one annotator is available, report the limitation instead of claiming adjudicated truth.

An LLM judge is an optional measurement tool, not ground truth. Freeze its rubric/model, blind method identity and randomize order, compare against human annotations, report false acceptance/rejection and agreement with uncertainty. Separate evaluators from generators where feasible; another model family alone does not establish independence. Automated results cannot establish semantic support without validation.

## Stopping and publication criteria
Proceed to full study only if (1) closest-work review leaves a substantive gap, (2) labels align with the task, (3) the effect survives a small independent feasibility check, and (4) resource estimates support the intended uncertainty analysis. Otherwise retain an engineering report or exploratory study. A paper needs a general finding or method, reproducible controls and external validation; fixing SciSpark's missing keywords alone is not research novelty.

Deliverables: related-work matrix, frozen protocol and split manifest, released reproducible harness where licenses permit, topic-level results and failure taxonomy, cost/workload frontier, limitations and scoped conclusions. Engineering data may motivate hypotheses but must not be represented as untouched validation.
