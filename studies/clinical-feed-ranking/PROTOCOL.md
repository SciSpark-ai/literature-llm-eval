# Expanded clinical-original pointwise comparison

Frozen before examining this run's results. User selected only the clinical-original evidence-producing pointwise relevance scorer, not Wiki, quote variant, their fusion, or an LLM judge. Model gpt-4o-mini-2024-07-18, temperature 0, 8192 output cap; original saved instructions and common single-object adapter from pointwise-comparison-v1. Each request sees one title and first 1800 abstract characters, verified exactly against the completed CE inputs. No rule gate before scoring. All 682 identities from the frozen expanded pool are included.

Reuse 63 exact cached request bodies; 619 new calls, four concurrent workers, no automatic retries. This is one observation per paper/configuration, including earlier cached observations, not a repeated independent run. It mixes request times. Clinical prompt choice followed exposed development experiments, so no held-out selection claim.

Primary comparison: raw grade ranking against CE on identical IDs; tie-expected nDCG@10, P@10, recall@50 and recall@100, separate abstract/full-text labels. Report unique score counts because coarse LLM ties matter. Quote and entry validation are separate attrition endpoints and do not silently change ranking. No global winner from three exposed topics. Population prevalence, clinician usefulness, provider timing stability and semantic quote entailment remain unmeasured. A future CE-to-LLM cascade must separately count candidate-stage omissions; it is not the current stand-alone ranking comparison.

Public-export note: the spending-authorization sentence was omitted; the original protocol hash is in data/export-provenance.json. This protocol predates the exploratory score combinations.
