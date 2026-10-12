# Adversarial novelty search: evidence-gated LLM document screening (verbatim-quote gate vs decoupled decision/evidence)

Search date: 2026-10-09. Scope: work that already answers, or closely approaches, the candidate question (how much relevant evidence is lost when a positive screening decision is admitted only if a generated verbatim quote passes exact-source verification, and whether decoupling decision from evidence extraction improves the recall / unsupported-decision / cost / human-workload tradeoff vs a joint decision+quote prompt with a hard gate).

Verification status legend used below: [FULL] = read beyond abstract (full text or substantial body via fetch); [ABSTRACT/SNIPPET] = verified only from abstract, search snippet, or landing page; [BLOG/DOC] = vendor documentation or blog.

---

## Key Question 1: Which items most directly overlap the candidate question, and exactly what remains unanswered by them?

### Takeaway
One 2026 preprint (Windisch et al., "Show Your Work", medRxiv) directly implements a label+verbatim-quote prompt on biomedical abstracts with an exact-substring validity check and reports coverage loss and quote-validity rates per model; it is the single closest item and would be the main prior-art citation. It does NOT test a hard gate on the positive class, does not decouple decision from evidence (two-call or sentence-ID), does not account for cost or human-review workload, and does not do screening/monitoring. No item found combines all components of the candidate question.

### Cited Findings

**1. Windisch et al. 2026, "Show Your Work: Verbatim Evidence Requirements and Automated Assessment for Large Language Models in Biomedical Text Processing" (medRxiv preprint; also indexed as PMC13252682) [FULL]**
- Task: classify oncology RCT eligibility scope (LOCALIZED / METASTATIC / BOTH / NEITHER, plus UNCLEAR abstain) from title+abstract of 200 RCTs (2005-2023, six journals); 3 runs x 3 models (gpt-5.2-2025-12-11, gemini-3-flash-preview, claude-opus-4-5-20251101), default settings. — [medRxiv full text](https://www.medrxiv.org/content/10.64898/2026.03.03.26346690v1.full.txt); [PMC record](https://pmc.ncbi.nlm.nih.gov/articles/PMC13252682/)
- Design: two independent conditions, label-only vs label + verbatim supporting quote in a single call (fixed two-line output: label line, quote line); "the two conditions were independent requests, so the evidence output could not condition on the baseline answer." No quote required for UNCLEAR. — same source
- Quote validity check: strict contiguous substring after collapsing whitespace runs and stripping surrounding quotation marks; "Quotes failing this check were recorded as invalid-quote regardless of label correctness." — same source
- Quote-validity rates (share of runs): GPT-5.2 83.3%, Gemini 3 Flash 91.2%, Claude Opus 4.5 91.2%. — same source
- LLM-judge semantic support of evidence-bearing predictions: GPT-5.2 73.8-78.8%, Claude 67.2-73.5%, Gemini 48.0-59.0%; "mechanically valid quotes are not equivalent to semantically sufficient evidence." — same source
- Coverage (non-abstain, non-invalid) baseline -> evidence-required: GPT-5.2 86.2% -> 84.3%; Gemini 98.3% -> 92.8% (invalid outputs 1.5% -> 5.0%); Claude 96.0% -> 94.5%. — same source
- Conditional macro-F1 baseline -> evidence: GPT-5.2 0.910 -> 0.916; Gemini 0.933 -> 0.945; Claude 0.828 -> 0.777 (majority-vote accuracy 0.785 vs 0.725, McNemar p=0.009). "Correct and mechanically valid" share: 77.0% / 86.2% / 70.8%. — same source
- Restricting to judge-supported predictions raises macro-F1 (e.g., representative judge: GPT-5.2 0.92->0.95, Gemini 0.94->0.95, Claude 0.78->0.88) at the cost of coverage. — same source
- Quote stability across runs (Jaccard): GPT-5.2 0.896, Claude 0.897, Gemini 0.664. — same source
- Not reported (verified by reading): positive-class recall under a gate, cost/latency, human-review workload, any sentence-ID/span-selection or two-call decoupled comparison. Stated future work: "multiple short spans, character offsets, or constrained decoding" as less brittle, still mechanically checkable evidence constraints; evidence-span stability as a primary endpoint. — same source
- Presented as a poster at an ASTRO meeting (session listing). — [ASTRO session](https://amportal.astro.org/sessions/pqa-03-22879/show-your-work-verbatim-evidence-requirements-and-automated-assessment-for-large-language-mod-113268)

**2. Raab et al. 2025, "Audit, Alignment, and Optimization of LM-Powered Subroutines with Application to Public Comment Processing" (arXiv 2507.08109) [FULL]**
- Task: environmental-review public comment processing; LM extracts concerns each with supporting free-text quotes in one subroutine; quotes post-processed with fuzzy string matching against the source letter (not exact match). — [arXiv HTML](https://arxiv.org/html/2507.08109)
- Sentence-level quote recall / precision vs SME-selected sentences: CFFF 47.0% / 90.7%; CPNP 30.1% / 58.0%; MBTA 17.9% / 80.8%; WS 23.5% / 72.7%; All 23.1% / 73.7%. "recall is strongly dependent on the length of the source document." — same source
- Offered explanations for low recall: long-context degradation; LM "may be biased towards selecting relatively few quotes"; task framing aiming only at most relevant quotes; SME "lumpers." — same source
- No joint-vs-separate-call comparison; batch SME review of outputs with a relational audit database; no SME workload/time accounting reported. — same source

**3. Kartac et al. 2026, "VetScore: Risk-Weighted Fact Verification for Veterinary Long-Form QA with Citations" (arXiv 2608.03675) [FULL]**
- Excerpt exact-match rates (regex, line-level / anywhere in source): Gemini 3.1 Pro 93.3/94.1%; Claude Opus 4.6 88.5/89.6%; Qwen 3.5 397B 84.4/87.3%; GPT-5 80.2/80.7%; DeepSeek V3.2 71.4/77.0%; Mistral Small 41.5/49.7%. — [arXiv HTML](https://arxiv.org/html/2608.03675)
- Fuzzy (ellipsis-bridged) matching raises GPT-5 from 80.2% to 92.6%; "GPT-5.4 tends to use ellipses frequently." Adding formatting-only matches -> 98.3/96.6/93.8/96.5/91.0/62.1%; adding faithful paraphrases -> 99.8/99.7/98.3/99.3/98.1/85.5%. — same source
- Mismatch classifier (Gemini 3.1 Pro) 0.89 accuracy / 0.89 macro-F1 vs 100 manual annotations (37 formatting, 44 paraphrase, 19 hallucination); for Mistral Small ~23% paraphrase, >14% fabricated. — same source
- Exact-match failure is NOT used as a gate on claims in VetScore scoring; no short-contiguous-span instruction described; prompts require excerpts with source ID and line indices. — same source

**4. Fagerberg et al. 2026, "Audited large language model triage for systematic review screening in national clinical guideline production" (medRxiv, Socialstyrelsen Sweden) [FULL]**
- Prospective deployment: 74,679 records across 24 SRs; 85.5% in AI-excluded pool; 0/600 audited AI-excluded records confirmed false negatives; estimated first-pass effort 415 -> 34 person-days (base case 1 min/record, 6 h/day; range 207->17 to 830->68); inference spend ~USD 400. Ensemble Gemini-3-flash + GPT-5.1, two runs each; any include/full-text vote by any run -> human. — [medRxiv full text](https://www.medrxiv.org/content/10.64898/2026.06.02.26354724v1.full)
- Output per record is a three-way decision plus a one-sentence reason described as auditable; NO verbatim quote requirement and NO automated quote verification/grounding check described. — same source

**5. Zabaleta & Lin 2026, "SciLitBench" (arXiv 2609.05505) [FULL]**
- Screening corpus of 42,981 records / 1,819 inclusions; 22 open-weight LLMs. Adding researcher-authored rationales of "verbatim evidence quotes paired with one-sentence justifications" to few-shot full-text prompts raised average F2 from 0.551 to 0.633. — [arXiv HTML](https://arxiv.org/html/2609.05505)
- Two-step scheme uses a refinement model to convert free-form answers into strict yes/no so decision quality is evaluated separately from format compliance; no abstention mechanism; no quote-validity or verification-induced-recall-loss metrics. — same source

**6. Galli, Gavrilova & Calciolari 2025, Information 17(5):501, "Validating Large Language Models for Title-Abstract Screening in Low-Prevalence Systematic Reviews: An Environmental Science Case Study" [ABSTRACT/SNIPPET only; MDPI page returned HTTP 403 twice]**
- Search snippet: prompt asks the model to quote a sentence from the title/abstract backing its decision and to output a fixed "no supporting text" message otherwise; pilot rounds "almost eliminate fabricated trial characteristics" because hallucinated fields are visible to the auditor; 500 records, 8 inclusions, five LLMs, one model with 1.00 sensitivity. No measured invalid-quote rate and no gate reported in the snippet. — [DOI](https://doi.org/10.3390/info17050501)

**7. McLaughlin, Walz & Arries 2026, "In Search of Ethical Procedures for LLM-Assisted Systematic Review Production" (medRxiv v2) [FULL]**
- Citation misattribution 7.06% (semi-automated) and 4.13% (fully automated) of cited claims, measured by manual keyword matching; verbatim criteria led the model to reject all 9 originally included full texts; no verbatim quote verification or gating in the pipeline; ReviewFoundry has an unevaluated "automated text-matching" feature. — [medRxiv](https://www.medrxiv.org/content/10.64898/2026.02.18.26346559v2.full)

**8. Anthropic Citations API documentation [BLOG/DOC]**
- Citations are returned as `char_location` (start/end char index) or block-index pointers into sentence-chunked documents, with `cited_text` extracted by the API; "citations are guaranteed to contain valid pointers to the provided documents"; "In Anthropic's evaluations, the citations feature is significantly more likely to cite the most relevant quotes from documents than purely prompt-based approaches"; cost saving because `cited_text` is not output tokens. No numbers published. — [Citations docs](https://platform.claude.com/docs/en/build-with-claude/citations)

**9. Madeyski, Kitchenham & Shepperd 2025/2026, "LLM4SCREENLIT" (arXiv 2511.12635 v2) [FULL, first 100k chars]**
- Recommends Lost Evidence (1-Recall), MCC and weighted MCC with explicit FN:FP cost ratios; "LLMs should identify unclassifiable papers as referred-back to a human reviewer"; referred-back papers "should be classified appropriately in confusion matrices, rather than reducing the total number of classified papers"; escalate to human-only review when Lost Evidence exceeds a threshold; "none of the five papers reporting workload savings incorporated FN costs." Does not discuss quote/rationale verification. — [arXiv HTML](https://arxiv.org/html/2511.12635v2)

### Inferences
- Windisch et al. is the only located work that operationalises "verbatim quote + exact-substring validity + abstention" on biomedical abstracts with current frontier models; it is best characterised as a measurement of quote-validity and coverage loss, not of a hard gate on positives, and it does not vary the evidence-elicitation mechanism.
- The pieces of the candidate question exist separately: quote-validity rates (Windisch; VetScore), quote-recall loss vs document length (Raab), referred-back accounting and Lost Evidence framing (LLM4SCREENLIT), prospective workload accounting for LLM screening without quotes (Fagerberg), span/index-based citation as an engineering alternative to free-text quoting (Anthropic docs). No source composes them into a gate-policy comparison.
- What remains unanswered by the closest items: (a) effect of a hard "no valid quote => not positive" gate on positive-class recall in a screening/monitoring task with relevance labels; (b) whether failures should be routed to human review and what that costs in reviewer workload; (c) joint single-call vs two-call decoupled designs, or sentence-ID/span selection vs free-text quoting, under the same gate; (d) cost accounting per admitted positive; (e) external validation across topics.

### Gaps
- Galli et al. 2025 full text could not be read (HTTP 403); whether they mechanically verified quotes is unverified.
- The last ~54k characters of Fagerberg et al. and ~45k characters of LLM4SCREENLIT were not read; later recommendations could mention rationale verification.

---

## Key Question 2: Has anyone published failure rates of exact-match verbatim quotes from GPT-4-class models on scientific abstracts, and the effect of "short contiguous span" instructions?

### Takeaway
Yes for failure rates on oncology RCT abstracts (Windisch et al.: 8.8-16.7% invalid quotes with GPT-5.2 / Gemini 3 Flash / Claude Opus 4.5 under strict whitespace-normalised substring matching) and on veterinary source texts (VetScore: 6-58% non-exact excerpts by model, most of which are formatting or paraphrase rather than fabrication). No source was found that tests the effect of a "short contiguous span" instruction.

### Cited Findings
- Invalid-quote share of runs on 200 oncology RCT abstracts: GPT-5.2 16.7% (83.3% valid), Gemini 3 Flash 8.8%, Claude Opus 4.5 8.8%; strict substring after whitespace normalisation; authors note the rule "may penalize multi-span evidence or minor normalization differences." — [Windisch et al. 2026](https://www.medrxiv.org/content/10.64898/2026.03.03.26346690v1.full.txt)
- Exact-match excerpt rates by model (line-level): 93.3% (Gemini 3.1 Pro) down to 41.5% (Mistral Small); GPT-5 80.2%, rising to 92.6% when ellipsis-bridged matching is allowed; faithful-paraphrase and formatting-only mismatches dominate over fabrication for frontier models. — [VetScore, arXiv 2608.03675](https://arxiv.org/html/2608.03675)
- Quote-selection sentence-level recall 17.9-47.0% (precision 58-91%) on public comment letters with fuzzy matching; recall declines with document length. — [Raab et al. 2025, arXiv 2507.08109](https://arxiv.org/html/2507.08109)
- Legal domain: models often fail to check whether quoted text actually appears in the cited passage (recall on hard examples ~36-61% for opinions). — [Verma, arXiv 2608.12571 (ABSTRACT/SNIPPET)](https://arxiv.org/pdf/2608.12571)
- Elicit's 2023 Factored Verification paper reports ~0.62 (ChatGPT-16k), 0.84 (GPT-4), 1.55 (Claude 2) hallucinations per paper summary; no quote-level exact-match statistics published; Elicit's support page says internal evaluations are run but numbers are not published. — [Elicit blog](https://blog.elicit.com/factored-verification-detecting-and-reducing-hallucinations-in-frontier-models-using-ai-supervision) [BLOG]; [Elicit support](https://support.elicit.com/en/articles/552897) [BLOG]

### Inferences
- The GPT-4-class (2023-2024 era) figure is absent; the reported numbers are for GPT-5-era models. A claim of novelty for "first exact-match failure rate on scientific abstracts" is NOT safe; a claim for "effect of span-length/contiguity instructions and of normalisation policy on gate-induced loss" appears safe.

### Gaps
- No source tests a "short contiguous span" instruction; Windisch et al. list "multiple short spans, character offsets, or constrained decoding" only as future work.
- No published vendor evaluation (Elicit, Consensus, Scite, SciSpace, Undermind, OpenEvidence, Semantic Scholar) with exact-quote validation failure rates was found; only secondary comparisons exist. — e.g. [IntuitionLabs review (secondary)](https://intuitionlabs.ai/articles/citation-reliability-ai-literature-reviews)

---

## Key Question 3: Has anyone evaluated routing quote-verification failures to human review with workload accounting?

### Takeaway
No. Workload accounting exists for LLM screening without quote gates (Fagerberg et al.: 415 -> 34 person-days; routing any non-unanimous exclusion to humans), and abstention/coverage accounting exists for citation verifiers (HALLMARK: 18-21% abstention routed to humans), but no source routes verbatim-quote verification failures to human review and costs it.

### Cited Findings
- Prospective screening deployment routes every record with any include/full-text vote to humans; person-day estimates 415 -> 34 base case; audits of AI-excluded pool found 0/600 confirmed FNs. No quote gate. — [Fagerberg et al. 2026](https://www.medrxiv.org/content/10.64898/2026.06.02.26354724v1.full)
- HALLMARK: a bibliographic citation verifier abstains on 18-21% of entries it cannot match to a backing record (coverage 0.79-0.82); at ~2% base rate FPR drives precision (~7x precision gap across verifiers); abstention raised recall for the conservative tool and bought precision for LLM verifiers. — [HALLMARK, arXiv 2607.18360 (ABSTRACT/SNIPPET)](https://arxiv.org/html/2607.18360v1)
- LLM4SCREENLIT recommends referred-back-to-human handling be kept in the confusion matrix and workload savings include FN costs; no rationale/quote verification. — [arXiv 2511.12635](https://arxiv.org/html/2511.12635v2)
- Raab et al.: SME batch review of concerns/quotes with audit database; "whether auditability can be provided without undue burden on SMEs is unresolved"; no time accounting. — [arXiv 2507.08109](https://arxiv.org/html/2507.08109)
- Pharmacovigilance: Evidence Prime ISPOR 2026 poster describes agent outputs with "supporting quotes, document location, and brief rationale" as an audit trail (F1 80% on suspected-drug tagging, n=50 test) but reports no quote verification or failure routing. — [ISPOR 2026 poster (ABSTRACT)](https://www.ispor.org/heor-resources/presentations-database/presentation-cti/ispor-2026/poster-session-3-3/from-text-to-signal-evaluating-llms-for-valid-case-identification-in-pharmacovigilance)
- Legal: "Who Checks the Citations?" GPT-5 agentic verification 82.8% recall / 60.5% F1 with ~16.9 steps per excerpt (cost noted); no human-routing accounting. — [arXiv 2606.21155 (ABSTRACT/SNIPPET)](https://arxiv.org/pdf/2606.21155)

### Inferences
- Routing gate failures (rather than discarding them) and expressing the tradeoff in reviewer workload per retained relevant item is not covered by any located source; this component of the candidate question appears open.

### Gaps
- Vendor screening tools (Covidence, Rayyan, DistillerSR, ASReview) did not surface documentation of LLM rationales or quote highlighting for screening decisions; only a 2024 ISPOR review mentions "auto-populating highlighted qualitative information" for extraction. — [ISPOR EU 2024 (ABSTRACT)](https://www.ispor.org/heor-resources/presentations-database/presentation/euro2024-4018/141969)

---

## Key Question 4: Are there 2025-2026 papers on evidence-grounded literature triage/monitoring or living evidence surveillance with LLMs that include these components?

### Takeaway
2025-2026 LLM screening/triage papers exist (Fagerberg; SciLitBench; Hu et al. Cochrane ESM; GREP-Agent; multi-LLM agreement), and some ask for rationales or use verbatim-quote rationales in few-shot examples, but none implements an exact-verification gate on positives, nor compares joint vs decoupled evidence elicitation, nor routes gate failures with workload accounting. "Living evidence surveillance with LLMs + verified quotes" was not found.

### Cited Findings
- SciLitBench: verbatim-quote rationales in few-shot prompts raised F2 0.551 -> 0.633; no verification gate; selective prediction listed as future work. — [arXiv 2609.05505](https://arxiv.org/html/2609.05505)
- Fagerberg et al.: prospective guideline-programme triage with one-sentence reasons, no quote verification. — [medRxiv](https://www.medrxiv.org/content/10.64898/2026.06.02.26354724v1.full)
- Pooled LLM screening accuracy (18 studies): title/abstract sensitivity 0.92, specificity 0.94. — [medRxiv meta-analysis (ABSTRACT)](https://www.medrxiv.org/content/10.64898/2026.03.17.26348656v1.full)
- GREP-Agent (epidemiological parameters) argues agentic screening suits living reviews and evidence surveillance, with reviewer control over agents; no quote gate reported in snippet. — [medRxiv (ABSTRACT)](https://www.medrxiv.org/content/10.1101/2025.08.11.25333429v2.full.pdf)
- Multi-LLM full-agreement screening argues screening is "less reliant on open-ended generation in which hallucinated content is more likely to arise"; no numbers on rationale validity. — [PMC13263951 (ABSTRACT)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13263951/)
- Pharmacovigilance screening: Li et al. 2024 (FDA) GPT-4/Claude 2 97% sensitivity, 67% specificity; reasoning explanations used as few-shot examples, not verified. — [Frontiers 2024 (ABSTRACT)](https://www.frontiersin.org/journals/drug-safety-and-regulation/articles/10.3389/fdsfr.2024.1379260/full)
- Decoupled designs in adjacent tasks: medical coding predicts codes first, then selects supporting sentences, then a separate verifier checks pairs (no joint baseline). — [arXiv 2311.13735 (ABSTRACT/SNIPPET)](https://arxiv.org/pdf/2311.13735); two-phase verbatim citation retrieval (analysis call, then tool-schema-constrained quote extraction) is a defensive publication with no data. — [TD Commons 8892](https://www.tdcommons.org/dpubs_series/8892) [FULL, short]; PaperTrail does single-pass claim+evidence extraction with programmatic span mapping and cosine<0.55 flagging, no unlocatable-evidence rate. — [arXiv 2602.21045](https://arxiv.org/html/2602.21045)
- Format-induced loss: "The Format Tax" finds format-requesting instructions alone cause most accuracy loss on reasoning tasks and that generating freeform first then reformatting recovers most of it; classification tasks are less affected per Tam et al. 2024. — [arXiv 2604.03616 (ABSTRACT)](https://arxiv.org/abs/2604.03616); [Tam et al. 2024, arXiv 2408.02442 (ABSTRACT)](https://arxiv.org/abs/2408.02442v2)
- Attribution surveys/benchmarks (ALCE; CitePretrainBench; sub-sentence citations) treat citation precision/recall for generation, not gated classification; CitePretrainBench notes sentence/paragraph identifiers "only improve slightly" and non-verbatim grounding remains the failure point. — [Cite Pretrain, arXiv 2506.17585 (ABSTRACT/SNIPPET)](https://arxiv.org/html/2506.17585v2); [ALCE](https://aclanthology.org/2023.emnlp-main.398)

### Inferences
- The candidate question's distinctive contribution, relative to all located work, is the combination: screening/monitoring relevance labels + hard exact-verification gate on positives + measurement of gate-induced relevant-evidence loss + comparison of elicitation mechanisms (joint vs two-call vs sentence-ID/span) + routing of failures to human review with workload and cost accounting + topic-level external validation. Windisch et al. must be cited and distinguished explicitly (different task semantics: eligibility-scope labels, no gate on positives, no decoupling, no workload).
- The Format Tax / "freeform then reformat" line provides theoretical motivation for the two-call hypothesis but has not been applied to evidence gates.

### Gaps
- No direct match found after searching. Queries run (WebSearch, standard/extended): "LLM systematic review screening verbatim quote verification hallucinated evidence sentences"; "LLM citation verification exact quote match failure rate scientific abstracts"; "Elicit quote verification hallucination rate extraction technical report"; "sentence selection vs free-text quote LLM attribution recall loss span selection grounding"; "LLM living evidence surveillance literature monitoring 2025 evidence-grounded triage"; "Zhuang 2024 ALCE citation verification abstain unverifiable escalate human review workload LLM"; "LLM extraction label and evidence jointly vs separately two-stage prompt comparison hallucinated rationale recall"; "structured output format constraints degrade LLM reasoning recall JSON classification"; "RobotReviewer Trialstreamer LLM 2025 PICO extraction span verification"; "Consensus OR Scite OR Undermind OR OpenEvidence technical report quote verification exact match"; "selective prediction LLM classification abstain when citation unverifiable human escalation workload"; "LLM quote attribution verbatim copying failure paraphrase sentence index selection grounding benchmark 2025"; "Show Your Work verbatim evidence requirements trial eligibility criteria"; "Format Tax LLM freeform then reformat"; "Covidence OR Rayyan OR DistillerSR OR ASReview AI screening highlights supporting text"; "legal document review LLM verified citations quote check reject unverifiable recall cost human review"; "LLM title abstract screening supporting sentence OR evidence sentence OR justification quote hallucinated percentage"; "pharmacovigilance literature monitoring LLM screening evidence quote verification human review workload"; "RobotReviewer OR Trialstreamer LLM Marshall Wallace 2024 2025 evidence extraction grounded spans"; "extract-then-decide OR quote-then-answer OR quote extraction first then classification two-step"; "LLM grounding sentence IDs OR sentence indices versus quoting spans hallucinated citations ablation 2025 2026".
- Not searched directly: Google Scholar / Semantic Scholar forward-citation chasing from Windisch et al. (preprint is from March 2026; citing works may exist); ACL Anthology 2026 proceedings by keyword; GitHub READMEs of screening tools; "Zhuang et al. 2024" could not be identified (ALCE is Gao et al. 2023) and should be clarified by the requester.
- RobotReviewer/Trialstreamer LLM-era successors with span verification were not found; only pre-LLM rationale-highlighting (2017) and 2023-2025 Wallace-group extraction papers without a verification gate surfaced.
