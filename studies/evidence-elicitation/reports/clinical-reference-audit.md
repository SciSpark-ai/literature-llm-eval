# Clinical reference-data audit

Status: metadata and label audit only. The production clinical matcher, query planner and judge have not yet been evaluated on these topics. No new annotations or paid calls.

## CLEF TAR intervention shortlist

| Original split | Topic | Subject | Candidate records | Abstract-positive | Final-content-positive | Abstract-positive/content-negative |
|---|---|---|---:|---:|---:|---:|
| Training | CD012347 | Psychological therapies for the treatment of depression in chronic obstructive pulmonary disease | 1098 | 16 | 11 | 5 |
| Testing | CD010558 | Psychological therapies for treatment‐resistant depression in adults | 2815 | 37 | 10 | 27 |
| Testing | CD010753 | Antidepressants for insomnia in adults | 2539 | 29 | 20 | 9 |

Every shortlisted PMID has one binary abstract label and one binary content label, with no duplicate topic-PMID rows. Content-positive/abstract-negative count is zero in these three pools. These are record counts, not necessarily unique studies.

## Why this is a useful next step

CLEF Task2 supplies an expert Boolean-search candidate pool and separate screening labels; it tests screening/ranking within that pool, not discovery of everything outside it. Task1 supplies review title/objective information for retrieval. The three downloaded Task1 protocols are brief objectives rather than complete operational eligibility specifications. Expert search strings are retained for audit but must not be supplied to an autonomous planner and then scored as if it independently produced them.

Keep the original Training topic as development and the two Testing topics as a provisional validation cohort. This is only three topics and cannot support broad clinical validation. Cross-topic document overlaps exist:
- CD012347__CD010558: 12 shared PMIDs.
- CD012347__CD010753: 5 shared PMIDs.
- CD010558__CD010753: 74 shared PMIDs.

For judge prompt fitting, remove or group development-overlap documents before creating validation examples and report the altered denominator; retain complete original pools for faithful benchmark reporting. Do not hide the shared test-topic documents or bootstrap every record as independent.

## Label compatibility with the actual Psychiatry product

The existing clinical feed matches watch facets and includes treatment, safety and other research. It is not a systematic-review eligibility screener. A review label0 does not automatically mean the paper should be excluded from a clinician feed. Full-text-only exclusions are especially unsuitable as hard abstract-level negatives.

First executable clinical task: freeze a watch configuration from each objective, using the actual clinical taxonomy and exposing any unsupported concept mapping. Fetch and freeze candidate title/abstract metadata. Run the unchanged clinical stages and report retention of abstract-positive records, final-content-positive retention as a secondary coverage metric, stage-specific losses, ungraded status and candidate reduction. Do not call label0 feed outputs false positives without a compatible target definition. A review-eligibility adapter with full criteria would be a separate experimental system.

Watch mapping risks: TRD is a narrower population than depression; psychotherapy and antidepressants are broad treatment families; depression with COPD needs the conjunction of two conditions. Verify these mappings before calls. Do not inject paper-specific answers learned from qrels into watch entries.

## SYNERGY alternatives

The pinned catalog identifies three relevant candidates:
- Oud_2018: adult borderline-personality-disorder specialized psychotherapy trials; detailed criteria include treatment duration and intervention completeness. Strong clinical-intervention candidate, but these restrictions exceed a simple disease/treatment watch entry.
- van_Dis_2020: longer-term CBT outcomes across anxiety-related disorders, with specific population/comparator exclusions. Potential second intervention dataset after label-stage and metadata audit.
- Brouwer_2019: prospective predictors of depression relapse/recurrence. Useful for other-research matching; not a treatment-effect benchmark.

Only catalog eligibility information has been audited for SYNERGY; its per-record labels/text availability and source provenance are not yet verified. Do not substitute this metadata audit for dataset readiness.

## Sources and reproducibility

- CLEF TAR pinned revision: `dbc13d02bb3e2f8ebc90e62ff47f5eb591e5ca20`; [Task2 documentation](https://github.com/CLEF-TAR/tar/blob/dbc13d02bb3e2f8ebc90e62ff47f5eb591e5ca20/2019-TAR/Task2/README.md).
- SYNERGY pinned revision: `dc2dadfdbb98eb1b4259604789abd640aa3b693e`; [catalog](https://github.com/asreview/synergy-dataset/blob/dc2dadfdbb98eb1b4259604789abd640aa3b693e/datasets.toml).
- Local source files and SHA256 fingerprints are retained under data/reference-audit and data_manifest/clinical-reference-audit.json.
- Source-query generation, metadata retrieval and clinical LLM evaluation remain subsequent stages; this report does not claim their completion.
