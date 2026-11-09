# Third-party data and prompt attribution

The redacted requests in `runs/` reproduce clinical relevance and evidence-extraction prompts from SciSpark Psychiatry, built on [SciSpark wiki](https://github.com/SciSpark-ai/scispark_wiki) at commit `435afcd`, together with the study's experimental variants. Copyright 2026 SciSpark contributors. These prompt materials retain the Apache License 2.0, copied in `LICENSES/Apache-2.0.txt`; the repository's MIT license does not replace it.

The topic metadata and relevance labels in `data/clef-labels-and-provenance.json` and the run configurations derive from [CLEF-TAR/tar](https://github.com/CLEF-TAR/tar), revision `dbc13d02bb3e2f8ebc90e62ff47f5eb591e5ca20`. The source MIT license is included in `LICENSES/CLEF-TAR-MIT.txt`. Please cite Kanoulas, Li, Azzopardi and Spijker, *CLEF 2019 Technology Assisted Reviews in Empirical Medicine Overview*.

The metadata manifest also records the revision of the SYNERGY dataset repository used during the source audit; no separate SYNERGY dataset is redistributed in this study.

Paper abstracts are redacted. Paper titles and short model-generated quoted excerpts remain in the frozen artifacts; these are not relicensed as original analysis code. The analysis scripts and reports are covered by the repository-root MIT license.
