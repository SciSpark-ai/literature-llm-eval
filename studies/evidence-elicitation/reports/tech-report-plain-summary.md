# What we studied and what we found, in plain English

Written for a reader with no AI background. Every number comes from `reports/e4-e5-v1.md` and `reports/clinical-decide-only-v1.md`.

## The setting

SciSpark is a tool that reads new medical papers and flags the ones a particular doctor cares about. Inside it is a language model, the same kind of AI that powers chat assistants. For each paper, the model is asked to do two things in a single step: give a relevance score from 0 to 4, and copy out the exact sentence from the paper that justifies the score. If the copied sentence cannot be found in the paper word for word, the tool assumes the model made something up and throws the paper away.

## What went wrong

Papers that were genuinely relevant were being thrown away. When we looked closely, the model had usually found the right paper. It had just copied the sentence badly: it joined two sentences with "...", or changed a word. The quote was wrong; the judgment was fine.

## What we first wanted to ask, and why we changed the question

The obvious question was "how many good papers are we losing this way?" Two things made us drop it. First, two research papers from earlier this year had already measured this. Second, when we re-checked our own failures with a more forgiving matcher, about 40% of them disappeared: the copied sentences were in the paper after all, with slightly different punctuation. That part was a bug in our checking code, not a research question.

While doing that, we noticed something more interesting. When we changed only the instruction about how to copy the sentence, the model's scores changed on 29 out of 100 papers. When we removed the "copy a sentence" requirement completely, scores changed again. So we asked: does asking the model for evidence change its answer?

## How we tested it

We froze 100 papers from three medical topics where human experts had already decided which papers were relevant. We sent them to the model under two versions of the instructions: the original (score plus quote in one step) and a stripped version (score only). The key design choice was to send each version four times, with every request identical down to the byte, so we could see how much the model changes its mind on its own. Without that, there is no way to tell a real effect from randomness.

Then we tested a different way to get the evidence: ask for the score first, and ask for the supporting sentence in a separate second request. We also tried a version where, instead of copying a sentence, the model just picks a sentence number from a numbered list, so the quote is always exactly right.

Every request was saved, every reply was cached, and a spending guard refused to go over a set budget. The whole set of experiments cost about 60 cents.

## What we found

**The model is wobblier than we thought.** The exact same request, sent four times, changed the score on 18 out of 100 papers and the keep-or-drop decision on 11 out of 100. On one topic, the same instructions kept 24, 34, 24 and 18 of the 37 relevant papers across four runs. We had guessed the wobble would be about half that. This is the most useful single number from the study, because it means that anyone who compares two versions of their instructions with one run each, which is the usual practice, is mostly looking at noise.

**Asking for evidence does change the answer, but not by enough to claim it.** Scores with and without the evidence requirement differed on 31 out of 100 papers. That is more than the wobble, but only 1.7 times more. Before running the experiment we had written down that we would need at least 2 times to call the effect real. It did not clear the bar, so we report it as "not established on three topics". There is a hint that the two versions disagree about how strongly a paper matches rather than about whether to keep it, but that came up after the fact and we label it as exploratory.

**Where the lost papers actually go.** The one-step version does not lose papers at the judgment stage. It loses them at the quote check: about half of its own quotes fail, and the paper goes with them. The score-only version keeps roughly the same papers but has no quotes to fail.

**The two-step design works and is affordable.** Asking for the score first and the quote second produced a checkable quote for 96 out of 100 kept papers; picking a sentence number produced one for 100 out of 100. The one-step design managed 45 out of 100. The two-step design costs about 1.65 times as much per paper sent, and less per paper that ends up with proof.

## What we conclude

1. Before comparing two versions of instructions to a language model, measure how much the answers change when nothing changes. On this model that was about 18 in 100. One run of each version is not a comparison.
2. If you need the model to show its evidence, ask for it in a separate step, or have it point at a sentence rather than copy one. Asking for everything at once throws away good answers for bad copying.
3. The claim we set out to test, that asking for evidence distorts the judgment, did not clear the bar we set. We do not make that claim.

## What this study is not

It covers three medical topics, one model, and a set of papers that was deliberately rich in relevant ones. It checked whether quotes were in the paper, not whether they actually supported the score. Humans did not re-check anything. It is a careful small study with repeatable code and honest numbers, not a general law.
