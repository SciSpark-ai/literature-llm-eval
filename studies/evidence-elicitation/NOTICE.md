# Notice: software and prompts from other projects

This study measures a product, and some frozen files quote that product's prompts word for word.

| What | Where in this folder | From | Licence |
|---|---|---|---|
| The general relevance-assessment prompt ("Assess paper relevance using this fixed rubric…") | `runs/wiki-clinical-v1/stage-a-requests.json` | SciSpark wiki, https://github.com/SciSpark-ai/scispark_wiki, file `src/lib/recommendation/assessment-skill.ts`, unchanged. Copyright 2026 SciSpark contributors. | Apache License 2.0, copy in `LICENSES/Apache-2.0.txt` |
| The clinical triage prompt ("You triage new psychiatry literature…") and the quote and match checks that the capture scripts load | `runs/*/stage-a-requests.json`; loaded by `scripts/*.mjs` | SciSpark Psychiatry, an independent, unofficial fork of SciSpark wiki taken at commit `435afcd`. These parts were written for the fork. | Apache License 2.0 |

This repository is not affiliated with or endorsed by the SciSpark project. The analysis code, harness and
reports here are the author's own and are under the MIT licence in the repository root.
