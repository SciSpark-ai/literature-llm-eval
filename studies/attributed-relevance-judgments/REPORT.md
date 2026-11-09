# Report: Attributed Relevance Judgments by LLMs in Biomedical Literature Screening

Results of E4 (repeated runs) and E5 (decoupled evidence extraction) on the frozen 100-candidate set. Read `RESEARCH_PLAN.md` first for the pre-stated hypotheses. Paths below refer to the private working tree; in this repository the generated analyses are under `results/` and scripts under `scripts/`.

## Controlled design
Frozen 100 candidates (75 abstract-positive, 25 sampled negatives) on three exposed CLEF TAR intervention topics; GPT-4.1-mini-2025-04-14, temperature 0. E4: four runs of the joint prompt (clinical-v1 plus three tagged repeats) and four of the decide-only prompt (clinical-decide-only-v1 plus three tagged repeats); requests byte-identical within arm, verified by `e4_verify_requests.py`; repeats distinguished only by the HTTP `user` tag. E5: extraction-only calls after the decide-only decision (free verbatim quote, D+E; numbered-sentence selection, D+S) and after joint quote failures (J+R), verified by a three-tier matcher (production exact, normalized, elided-in-order).

Deviations from the plan are summarized below from the original E4/E5 checkpoint log (kept in the private working repository):
- The joint repeats are `e4-joint-r2`, `e4-joint-r4` and `e4-joint-r5`. `e4-joint-r3` stopped at request 4 of 7 with a transport read error; it was not retried and is excluded. The owner authorized `e4-joint-r5` as a fresh full repeat under a new tag.
- The owner raised the paid-API ceiling from 10 to 20 dollars during E4, because concurrent jobs on the shared ledger had consumed the planned headroom. The reservation formula and the no-retry rule are unchanged.
- In one D+E batch and one J+R batch the model returned fewer entries than papers. A missing entry is recorded as no evidence (flag `omitted`) and counted as unverified; duplicated or out-of-range indices still abort the parse.
- The joint run's own quotes are scored with the same three tiers as the extraction arms, and J+R keeps the better of the original and the retried evidence. The exact tier reproduces the production `quoteVerified` verdict on all 72 graded joint records.

## E4 results
| Quantity | Value |
|---|---:|
| within-joint raw flip rate (mean of 6 pairs) | 0.182 |
| within-joint flip rate at grade>=1 | 0.128 |
| within-joint flip rate at grade>=2 | 0.082 |
| within-decide raw flip rate (mean of 6 pairs) | 0.182 |
| within-decide flip rate at grade>=1 | 0.088 |
| within-decide flip rate at grade>=2 | 0.085 |
| between-arm raw flip rate (mean of 16 pairs) | 0.306 |
| between-arm flip rate at grade>=1 (mean of 16 pairs) | 0.134 |
| between-arm flip rate at grade>=2 (mean of 16 pairs) | 0.185 |
| topic-level between minus within, mean [95% bootstrap] | 0.117 [0.067, 0.159] |

| Arm | Topic | Threshold | Positives retained per repeat | Mean |
|---|---|---:|---|---:|
| joint | CD010558 | 1 | [24, 34, 24, 18] | 25.0 |
| joint | CD010558 | 2 | [18, 20, 16, 13] | 16.8 |
| joint | CD010753 | 1 | [22, 20, 21, 21] | 21.0 |
| joint | CD010753 | 2 | [21, 16, 17, 20] | 18.5 |
| joint | CD012347 | 1 | [16, 16, 16, 16] | 16.0 |
| joint | CD012347 | 2 | [14, 14, 14, 14] | 14.0 |
| decide | CD010558 | 1 | [34, 26, 34, 34] | 32.0 |
| decide | CD010558 | 2 | [13, 17, 12, 12] | 13.5 |
| decide | CD010753 | 1 | [22, 21, 22, 21] | 21.5 |
| decide | CD010753 | 2 | [14, 13, 14, 19] | 15.0 |
| decide | CD012347 | 1 | [16, 16, 15, 16] | 15.8 |
| decide | CD012347 | 2 | [12, 12, 11, 12] | 11.8 |

| Topic | Positives | Joint, quote exact, per repeat | Joint, quote any tier, per repeat | Joint any-tier mean | Decide-only grade>=1 mean | Gain (points of recall) |
|---|---:|---|---|---:|---:|---:|
| CD010558 | 37 | [18, 29, 22, 11] | [19, 29, 22, 11] | 20.25 | 32.00 | 31.8 |
| CD010753 | 22 | [6, 5, 7, 5] | [11, 15, 14, 10] | 12.50 | 21.50 | 40.9 |
| CD012347 | 16 | [4, 4, 4, 4] | [9, 6, 9, 7] | 7.75 | 15.75 | 50.0 |

The third table is the comparison go/no-go criterion 2 asks for: positives the joint prompt keeps once its own quote must verify (grade above 0 and the quote passes a matcher tier), against positives the decide-only prompt admits.

Grade distributions per run (count of records at each raw grade):

| Arm | Run | 0 | 1 | 2 | 3 | 4 |
|---|---|---:|---:|---:|---:|---:|
| joint | clinical-v1 | 28 | 17 | 0 | 7 | 48 |
| joint | e4-joint-r2 | 19 | 29 | 0 | 7 | 45 |
| joint | e4-joint-r4 | 30 | 22 | 0 | 6 | 42 |
| joint | e4-joint-r5 | 36 | 16 | 2 | 8 | 38 |
| decide | clinical-decide-only-v1 | 18 | 42 | 0 | 0 | 40 |
| decide | e4-decide-r2 | 27 | 30 | 0 | 0 | 43 |
| decide | e4-decide-r3 | 20 | 42 | 0 | 0 | 38 |
| decide | e4-decide-r4 | 16 | 40 | 0 | 10 | 34 |

H-A1 (within-prompt raw flip rate below 10 percent; binary flip rate below 5 percent): not supported. The mean within-prompt raw flip rate is 0.182 in both arms (range over the twelve pairs 0.06 to 0.30), and the mean flip rate at grade at least 1 is 0.108 (joint 0.128, decide-only 0.088). Both are about twice the hypothesized bound.

H-B1 (between-prompt flip rate above twice the within-prompt rate, bootstrap interval excluding zero): not supported. The between-prompt raw flip rate is 0.306, which is 1.686 times the within-prompt rate, below the pre-stated factor of two. The topic-level difference is positive on all three topics, 0.117 [0.067, 0.159], so the prompts do differ beyond noise, but with three topics the bootstrap interval is simply the range of the three topic values and carries little weight. At the grade-at-least-1 cut the between-prompt flip rate is 0.134 against 0.108 within, so almost none of the binary admission difference exceeds noise; at grade at least 2 it is 0.185 against 0.082 (joint) and 0.085 (decide-only) within, so the prompts disagree mainly about how strong a match is, not about whether to admit.

## E5 results
| Policy | Topic | Admitted positives | Verified exact | Verified any tier | Negatives admitted | Negatives verified |
|---|---|---:|---:|---:|---:|---:|
| J | CD010558 | 24 | 18 | 19 | 3 | 3 |
| J | CD010753 | 22 | 6 | 11 | 1 | 0 |
| J | CD012347 | 16 | 4 | 9 | 6 | 5 |
| J+R | CD010558 | 24 | 24 | 24 | 3 | 3 |
| J+R | CD010753 | 22 | 15 | 16 | 1 | 0 |
| J+R | CD012347 | 16 | 14 | 15 | 6 | 6 |
| D+E | CD010558 | 34 | 34 | 34 | 5 | 5 |
| D+E | CD010753 | 22 | 22 | 22 | 0 | 0 |
| D+E | CD012347 | 16 | 13 | 13 | 5 | 1 |
| D+S | CD010558 | 34 | 34 | 34 | 5 | 5 |
| D+S | CD010753 | 22 | 22 | 22 | 0 | 0 |
| D+S | CD012347 | 16 | 16 | 16 | 5 | 5 |

| Policy | Tokens in | Tokens out | USD | Verified positives | USD per verified positive | Token ratio vs J |
|---|---:|---:|---:|---:|---:|---:|
| J | 42592 | 6989 | 0.0282 | 39 | 0.00072 | 1.00 |
| J+R | 58073 | 8132 | 0.0362 | 55 | 0.00066 | 1.34 |
| D+E | 74767 | 6942 | 0.0410 | 69 | 0.00059 | 1.65 |
| D+S | 78720 | 4616 | 0.0389 | 72 | 0.00054 | 1.68 |

Tier counts: {"J": {"exact": 33, "normalized": 0, "elided": 14, "none": 25}, "J+R": {"exact": 62, "normalized": 1, "elided": 1, "none": 8}, "D+E": {"exact": 75, "normalized": 0, "elided": 0, "none": 7}, "D+S": {"exact": 82, "normalized": 0, "elided": 0, "none": 0}}

Totals over the three topics: J admits 62 positives, 28 verified at the exact tier and 39 at any tier; J+R 53 exact and 55 at any tier; D+E admits 72, 69 verified, all exact; D+S admits 72, 72 verified, all exact.

H-C1 (verified evidence for at least 90 percent of admitted positives under D+E; 100 percent lexical validity under D+S): supported. D+E verifies 69 of 72 admitted positives (0.958). Every quote the model returned passed the production exact tier; the three unverified positives are papers for which the model returned no entry at all (seven grade-1 papers omitted in one CD012347 batch, three of them positive). D+S returned an in-range sentence for all 82 items, so 72 of 72 admitted positives (1.000) are lexically valid by construction.

H-C2 (D+E tokens at most 2.5 times the joint prompt): supported. D+E uses 1.65 times the joint prompt's tokens in total (D+S 1.68, J+R 1.34). Per admitted positive the ratio is 1.42 (81,709 tokens over 72 positives against 49,581 over 62).

## Interpretation
The temperature-zero grader is far noisier than assumed: byte-identical requests change 18 percent of raw grades and 11 percent of admit decisions between runs, and on the narrow-population topic CD010558 the joint prompt retained 24, 34, 24 and 18 of 37 positives across four runs. The E3 observation that decide-only and joint differ on 29 of 100 grades is therefore mostly noise: two runs of the same prompt differ on about 18. A coupling effect remains, concentrated above the admission cut. The grade-scale collapse under decide-only is real but not absolute: three of four decide-only runs never used grade 3 and the fourth used it ten times, and decide-only retains fewer positives at grade at least 2 on every topic on average (13.5, 15.0, 11.8 against 16.8, 18.5, 14.0). Decoupling does what it was designed to do for evidence: a second extraction call yields production-valid quotes for 96 to 100 percent of admitted positives at about 1.65 times the tokens, against 45 percent for the joint prompt at the exact tier and 63 percent with the tolerant matcher; the retry baseline J+R reaches 89 percent at 1.34 times the tokens. For Direction 2, criterion 1 (coupling above twice the noise) fails at 1.69, criterion 2 (decide-only recall above joint recall by at least 3 points on two of three topics after an elision-tolerant matcher) is met on all three topics: with the tolerant matcher applied to each joint run's own quotes the joint prompt keeps on average 20.25 of 37, 12.50 of 22 and 7.75 of 16 positives, against 32.00, 21.50 and 15.75 admitted by decide-only, so most of the joint prompt's lost recall comes from the quote gate, not from the decision (before the gate the raw-grade gain exceeds 3 points on CD010558 only: 32.0 against 25.0 of 37; 21.5 against 21.0 of 22; 15.8 against 16.0 of 16); criterion 3 is met on its own terms. The no-go rule fires on criterion 1 alone. The finding worth carrying forward is the noise floor itself: single-run comparisons of prompt variants on this grader are not interpretable.

## Limitations
Three development topics; sampled negatives, not realistic prevalence; one model; `user` tag assumed inert; the schema still carries a `quote` field in the decide-only arm; evidence support is lexical only, not semantic; no human annotation. Further limits found during execution: every run reported a different `system_fingerprint` (the two reference runs share one), so the measured noise includes backend variation and is not pure sampling noise; within-arm pairs share runs and are not independent; E5 used one decision run per arm, so its counts inherit the run-to-run noise measured in E4; lexical validity is not relevance (D+S verifies evidence for all 10 admitted negatives and D+E for 6 of 10); the J+R extraction prompt is not the production prompt, so J+R is a research baseline, not a production retry.

## Cost and artifacts
- E4 estimated model cost 0.16544 dollars (six complete runs plus the partial `e4-joint-r3`, 0.01218); E5 0.04138 dollars (D+E 0.01775, D+S 0.01561, J+R 0.00802). Conservative reservations: E4 2.899631 dollars over 46 requests, including one failed request of unknown cost; E5 0.707576 dollars over 15 requests. Cumulative reservation on the shared ledger immediately after the last E5 call: 13.052184 dollars against the 20-dollar ceiling; other jobs share the ledger.
- Run directories: `runs/e4-joint-r2`, `runs/e4-joint-r4`, `runs/e4-joint-r5`, `runs/e4-decide-r2`, `runs/e4-decide-r3`, `runs/e4-decide-r4`, `runs/e4-joint-r3` (partial, excluded), `runs/e5-decide-quote`, `runs/e5-decide-sentence`, `runs/e5-joint-retry`, `runs/e4`, `runs/e5`.
- Scripts: `e45_lib.py`, `e4_capture.mjs`, `e4_verify_requests.py`, `e4_paid.py`, `e4_analysis.py`, `e5_extract.py`, `e5_analysis.py`; tests in `tests/test_e4_e5.py`. `pilot_core.py` clamps the ceiling at 20 dollars with the default still 10.
- No product source changes. No new human labels.
