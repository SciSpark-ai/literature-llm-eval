# Controlled grading and model-settings comparisons

Status: development protocol. Existing clinical topics are exposed and must not be presented as an untouched test set.

## Ordered contrasts
1. Frozen clinical baseline versus contiguous-quote instruction. Same candidates/order/batches, model snapshot, temperature, schema and text. Retain the existing evidence validator. Evaluate quote validity, pre-validation relevance grades, post-validation eligibility, positive retention and sampled control retention separately.
2. Wiki fork-baseline rubric versus Psychiatry rubric on a common pool. Supply equivalent clinical facts through each native context schema, disable memories, use the same model and common visible source text. Native preprocessing and thresholds are separate analyses. The current baseline's psychiatry prefilter must not define the pool for an unrestricted end-to-end Wiki comparison.
3. Cross-encoder versus LLM raw relevance. Same query facts, document visibility and candidates. No quote penalties in the pure-ranker comparison. Record truncation and tie handling; require sufficient negative candidates before making ranking-quality claims. The positive-enriched 112-record diagnostic is not representative of deployment prevalence.
4. Repeat the key rubric contrast on one additional priced, explicitly budget-guarded model snapshot. Model choice and rates must be verified before calls. Compare the direction of the effect, not just the winning number.
5. Small repeated-run/batch-size study. Freeze all other inputs. Temperature zero is not assumed deterministic. Keep repeats distinct from cached replay. Count costs for every actual request.

## Frozen settings and accounting
For every run persist model identifier, prompt hash, temperature, any sampling defaults, maximum output tokens, input truncation, candidate order, batch size, schema mode, retries, validation code hashes, usage, latency and failure outcomes. A normal completion is not evidence of semantically correct output.

The shared user ceiling remains $10. Existing reservations intentionally overcount actual spending. An internal ranking lane was initially limited to $4; further calls must respect that guard or explicitly document a reallocation within the unchanged user ceiling before execution. Do not reset the ledger or bypass uncertain charges.

## Decisions deferred
Do not merge the taxonomy and domain text-word configuration merely because the two overlap. First separate a shared concept source from stage-specific policies. No vocabulary architecture or production prompt changes are authorized by an experimental improvement alone; report the concrete proposed behavior and evidence before implementation discussion.
