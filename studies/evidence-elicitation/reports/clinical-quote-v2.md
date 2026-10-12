# Contiguous quotation instruction: paired development probe

## Controlled change
Seven frozen request pairs differ only by this added system instruction:

> Quote extraction requirement: Return ONE short, exact, contiguous excerpt of 8-160 characters copied from the provided title or abstract. Do not paraphrase, concatenate separate passages, insert ellipses, or add words. Choose a passage supporting the relevance judgement; a treatment-result summary is not required.

Same 100 candidates, order, batches, visible text, schema, temperature 0 and GPT-4.1-mini-2025-04-14. Existing production validation is unchanged. The original rule-stage exclusions remain. Request equality was asserted after removing the appended instruction. All seven batches succeeded; no candidates were ungraded. Product files and vocabulary configuration were unchanged.

## Results
Reference-positive counts below use the existing abstract-screening labels. Eligibility is before final feed list caps, not actual displayed items.

| Topic | Positive candidates entering LLM | Baseline retained | Variant retained | Baseline positive quote failures | Variant positive quote failures |
|---|---:|---:|---:|---:|---:|
| Depression in COPD |16|4|13|12|1|
| Treatment-resistant depression |37|15|12|6|6|
| Antidepressants for insomnia |22|6|21|16|0|
| Total |75|25|46|34|7|

Seven additional insomnia reference positives were already excluded before the LLM in both conditions; denominators must not imply all 82 reference positives reached the model. Sampled negative-control retention remains 1, 0 and 0 across topics in both runs. This is not an estimate of deployment precision.

The original entry relevance grade changed for 29/100 candidates between runs (2/26 COPD, 15/44 resistant depression, 12/30 insomnia). Therefore the instruction affects more than the visible quote output, or residual run variability contributes, or both. With one run per condition, these possibilities cannot be separated. Temperature zero does not supply a replication guarantee.

The decrease in invalid quotes is encouraging, but the resistant-depression topic regresses in retained positives. Do not claim universal improvement, improved semantic relevance, or a held-out benchmark gain. These are exposed development topics and quote validity is only lexical source matching, not semantic support.

## Cost and reproducibility
New estimated cost: $0.0263648. Conservative reservation: $0.440855. Shared cumulative reservation: $3.891059, within the $10 user ceiling. Output caps were unchanged at 8192 tokens. No paid retries.

- `runs/clinical-quote-v2/`: frozen requests, responses, per-paper results and comparison JSON.
- `scripts/clinical_quote_v2.mjs`: capture/replay through production grading and verification with the experimental appended instruction.
- `scripts/clinical_quote_paid.py`: guarded paid transport.
- `scripts/clinical_quote_compare.py`: descriptive paired counts.

## Next decisions
Keep this variant experimental. Compare the Wiki rubric and cross-encoder on common visible inputs, separating raw relevance from evidence validation. Diagnose the resistant-depression failures and replicate selected fixed inputs before attributing score changes to a prompt effect. Future held-out topics must be separate from these development cases. See `model-settings-comparison-protocol.md` for the ordered model/settings contrasts.
