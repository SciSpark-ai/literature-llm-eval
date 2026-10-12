# Track A — Practical engineering evaluation

> **Audit revision (2026-10-09):** Prospective execution order and corrected interpretation are governed by [audit response](audit-response-and-revised-plan.md). Research remains a feasibility hypothesis; no new paid block should start before provenance and budget reconciliation.

Status: execution roadmap, 2026-10-09. Governs engineering prioritization; historical reports remain valid records, not product-wide validation. Companion: `research-protocol.md`.

## Objective
Choose a defensible next SciSpark Psychiatry pipeline under limited implementation time and the existing $10 total paid-API ceiling. Optimize observable user-facing behavior, maintenance burden and cost. Each experiment must end in a component decision: keep, change, remove, or insufficient evidence. Comprehensive means covering every consequential boundary, not exhaustively testing every configuration.

## Evaluation map
| Priority / boundary | Test | Evidence and metrics | Decision enabled |
|---|---|---|---|
| P0 Data acquisition/storage | Identifier coverage, missing abstract/date/type, deduplication, full versus truncated MeSH, cache replay | Record/field coverage, duplicate merges, missing-positive denominator, provenance | Preserve necessary metadata; separate display limits from storage |
| P0 Cleaning | Frozen numeric/negation/markup regressions and sampled real records | Changed critical tokens, exact source linkage, per-case diffs | Adopt verified fixes; re-embed only records whose embedding text changed |
| P0 Query/retrieval | Freeze PubMed query, timestamp, date semantics, IDs, ordering, cap and truncation; distinguish corpus coverage from query coverage | Known-reference recall, request failures, candidate count, latency, cost; out-of-label results reported unjudged | Query formulation and limits; no claim that unjudged results are irrelevant |
| P0 Domain/design filters | Apply each gate separately to common candidate inputs | Incremental and cumulative positive loss, negative retention, drop reasons, missing-type behavior | Remove or soften unsupported hard exclusions; decide shared concept source separately from stage-specific policies |
| P0 Relevance | CE, Wiki rubric, clinical rubric on identical visible candidates and interest facts | nDCG@10, recall at fixed reading budgets, threshold curves, ties, cost, latency | Select simple effective scoring approach; do not add CE+LLM unless incremental value justifies cost |
| P0 Evidence/match checks | Same saved outputs before/after quote and deterministic match checks | Positive losses; lexical validity separate from semantic support; missing fields/failures | Decide whether failure means exclusion, uncertainty, or review routing |
| P1 Final feed selection | Fixed grades; compare score-only with layers, journal priority and quotas | Relevant items displaced, per-topic coverage, redundancy, recency mix | Keep only justified selection rules; prestige is not evidence quality |
| P1 Cards | Title/result/population/comparator/number extraction, source linkage and negative findings | Automated consistency flags first; final stratified human faithfulness audit | Choose supported wording and fallback; rule pass is not factual proof |
| P1 Evidence map/notes | Trace counts and links back to papers; duplicates, overlapping studies, refresh/export | Deterministic count/link fixtures and source traceability | Accurate organization, no unsupported pooled-effect claims |
| P0 Runtime | Provider failure, timeout, rate limit, invalid JSON, missing abstract, stale cache | Completion/unknown rates, replay, stale-result labeling, no duplicate charging, measured usage | Reliable hosted/local behavior and graceful failure |

## Resource-bounded execution
Days 1–2: freeze manifests and engineering decision register; complete metadata/filter diagnostics. Days 3–4: expanded fixed-pool ranker comparison, only after checking failures and budget. Days 5–6: a few representative PubMed snapshots and final-selector replay. Days 7–8: card/source consistency and runtime fault checks. Days 9–10: minimal product changes with meaningful regressions, followed by one integration replay; reserve user annotation for the end. This is an effort schedule, not a promise that a publication is completed in ten days.

Use existing labels and offline replay first. Human work is limited to tasks existing labels cannot answer. Do not fabricate pass thresholds: deterministic corruptions and silently lost records are defects; statistical tradeoffs require a stated reading budget and an explicit uncertainty/coverage decision. Adopt a more complex component only when improvement is meaningful across topics without unacceptable losses, cost or latency. Otherwise prefer the simpler baseline and mark uncertainty.

## Existing evidence and outstanding work
- TREC component studies: engineering diagnostics on a nonofficial, exposed local corpus; not product superiority.
- Clinical rules: metadata truncation and incomplete domain coverage identified; fixes remain experimental.
- Quote variant: positive quote failures 34 to 7 on exposed topics; relevance scores also changed; no universal gain.
- Small-pool Wiki/CE/clinical comparison complete, rank metrics saturated.
- Expanded pools: 682 records ready; only first CE topic complete; HTTP 429 halted subsequent execution. No automatic retry; preserve unknown costs and audited recovery.
- Actual PubMed retrieval, full-pool LLM comparison, final selector/card evaluation, independent topics and human faithfulness audit remain incomplete.

## Budget and reporting
Update 2026-10-09: the user authorized raising the internal ranking lane from $6 to $10, equal to the user ceiling. Cumulative conservative reservation at that time: $5.973328; actual estimated spend: $0.334865. New paid scripts set `Budget(..., lane_limit_usd=10)`; the per-request reservation, no-retry and ledger rules are unchanged.

Update 2026-10-09 (later, during E4): the user raised the total paid-API ceiling and the ranking lane from $10 to $20. Cumulative conservative reservation at that time: $7.254226. `pilot_core.Budget` now clamps at $20 with the default still $10; only `e4_paid.py` and `e5_extract.py` pass `limit_usd=20`. The reservation formula, no-retry and ledger rules are unchanged.

As of expanded CE halt, conservative shared reservations $4.500162; actual usage lower, failed-call cost may be unknown. User cap remains $10; internal ranking allowance $6. No reset of ledger. Before any new block, estimate full request cost and reserve headroom for failures; reduce scope rather than silently exceeding the ceiling. A second provider/model is optional until the core comparison is useful.

Deliverables: stage-level loss diagram, per-component decision register with evidence/limitations, reproducible manifests and reports, and a proposed next pipeline. Product deployment choice is separate from model quality. Research findings may inform engineering only with their development/test status stated.
