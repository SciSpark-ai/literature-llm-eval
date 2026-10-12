# literature-llm-eval

Evaluation studies of how a large language model behaves at each stage of a literature-monitoring system. The system under study is SciSpark Psychiatry, a tool that retrieves new PubMed papers for a clinician, decides which are relevant, extracts supporting evidence, writes a summary card and checks it. Each study here isolates one stage, freezes every request and response, and regenerates every reported number from those frozen files.

Each study is self-contained in its own folder under `studies/` with its own README, reports, frozen runs, scripts and tests. Studies are added only when they are frozen: requests, responses and analysis fixed, numbers regenerable, limitations written.

| Study | Stage | Question in one line | Status | Headline |
|---|---|---|---|---|
| [`evidence-elicitation`](studies/evidence-elicitation/) | decide relevance, extract evidence | When the model must quote its evidence, how often does the check fail, does the requirement change the decision beyond run-to-run noise, and does a second extraction step recover verifiable evidence at what cost? | frozen; relevance labels human (CLEF TAR 2019), quote support model-checked only; three development topics, one model | Identical requests at temperature 0 change 18% of grades and 11% of keep-or-drop decisions; the prompt effect (31%) is 1.7× that noise, below the pre-stated 2× bar; decide-then-extract yields verifiable evidence for 96 to 100% of kept papers versus 45% in one step, at 1.65× tokens |

Status words: **frozen** (artifacts fixed, numbers regenerable), **model-labelled** (rests on model outputs), **human-labelled**, **written up**, **planned**.

## Reading order

1. The study's plain-English summary: `studies/evidence-elicitation/reports/tech-report-plain-summary.md`.
2. The study README for reproduction and limitations.
3. The full run report, `reports/e4-e5-v1.md`, and the related-work matrix under `literature/`.

## What is shared across studies

Nothing yet. The first study carries its own copy of the guarded API harness (`scripts/pilot_api.py`, `scripts/pilot_core.py`) and spend ledger. When a second study is frozen, whatever both need moves to a top-level `shared/` folder.

## Data

Paper abstracts are not redistributed. Studies ship PubMed IDs, titles, labels, model outputs and short quoted excerpts, plus a script that refetches abstracts from NCBI for local analysis. Relevance labels come from CLEF 2019 Technology-Assisted Review, which its organisers publish under the MIT licence; the licence text and attribution travel with the files.

## License

Code: MIT (`LICENSE`). Labels and abstracts under their own terms, see each study's README.
