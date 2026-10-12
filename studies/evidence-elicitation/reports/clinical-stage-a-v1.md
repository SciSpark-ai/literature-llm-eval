# Production clinical Stage A: first retention probe

## Execution
Seven requests, 100 candidates surviving the unchanged baseline rule gates, GPT-4.1-mini-2025-04-14, temperature 0, output cap 8192. All seven responses ended normally and replayed through production `gradeStageA` without failed batches or ungraded candidates. Production `verifyMatchedParts` and `layerOf` were then applied; model-design exclusion was mirrored from feed orchestration. No live retrieval, final feed quotas, deduplication, digest generation or ranking quality is evaluated.

The actual production prompt and schema were captured using an offline provider override. The guarded OpenAI transport used native JSON schema with strict=false and the same schema keyword sanitization as the product adapter; paid retries and correction calls were disabled. This is one model configuration, not a claim about every user-configured model. Responses are cached and replayable. Source hashes were checked against the prior rule baseline before capture and replay.

## Reference-positive retention
| Topic | Abstract-positive reference | Entered Stage A | After model judgement and quote validation | After deterministic match verification | After model-design gate |
|---|---:|---:|---:|---:|---:|
| Depression in COPD |16|16|4|4|4|
| Treatment-resistant depression |37|37|15|15|15|
| Antidepressants for insomnia |29|22|6|6|6|

These counts mean eligibility before final list limits, not displayed feed items. Seven insomnia positives were already lost to the unchanged domain gate. The earlier experimental rule fixes were deliberately not applied in this baseline run.

Of the 75 reference-positive papers reaching Stage A, 34 received a model entry grade above zero but failed quote verification: 12 COPD, 6 resistant-depression, 16 insomnia. The production implementation zeroes their grades. The remaining loss must not all be labelled semantic model error: existing review inclusion and clinical watch matching are different targets, and the simplified watches do not reproduce complete review protocols.

Examples of failed quotes contain ellipses joining separate fragments or paraphrased wording despite the verbatim instruction. This establishes extraction-format failure, not necessarily fabricated scientific findings. A follow-up must distinguish copied contiguous spans, omitted spans, and unsupported statements. Do not relax evidence verification simply to raise retention.

Deterministic match verification and model-design exclusion caused no further reduction in these reference-positive counts; upstream quote failures already removed many candidates, so this does not establish those later checks are harmless in general.

## Costs and validation
- New estimated model cost at the guarded list rates: $0.0282192.
- Conservative additional reservation: $0.437305; shared cumulative reservation: $3.450204, below the user's $10 ceiling.
- Seven successful batches; zero ungraded records.
- Research tests: 38 passed, including an explicit bounded 8192-token guard test. Default output cap remains 4096 for other experiments.
- No product source changes. No new human labels.

## Interpretation and next comparison
The largest observed Stage A loss here is failure to return a verifiable quotation. Therefore improving retrieval or changing the number of vocabulary files alone cannot resolve current retention.

Keep the baseline frozen. The next controlled prompt variant should request one short contiguous copied span, explicitly forbid ellipses and paraphrase, and retain the existing validator. Compare paired outcomes and costs on the same candidates; do not claim held-out improvement on these development topics. Model-based relevance and quote extraction should have separate metrics. A later independent topic set is necessary.

Vocabulary architecture remains undecided. Prior rule ablations support a shared source of clinical concepts, but do not demonstrate that all retrieval expansion and domain-admission policies should be collapsed into one undifferentiated list.

## Reproduction and artifacts
`clinical_stage_a.mjs capture` freezes actual requests; `clinical_paid.py --run` is explicitly paid and budget guarded; `clinical_stage_a.mjs replay` evaluates cached responses without network; `clinical_stage_report.py` creates counts. Artifacts are under `runs/clinical-v1/stage-a-*`. The selected sample is positive-enriched and cannot estimate feed precision or real-world accuracy.
