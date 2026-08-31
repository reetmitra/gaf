"""The two loops — the only control flow a reader has to follow.

Fast loop, per response: deterministic prep, two independent coders against a frozen
snapshot, structural then semantic checks, a deterministic router, integration.
Slow loop, per checkpoint: health metrics, a refactor proposal as an edit script, a
human gate, a new snapshot.

If this cannot be printed in a methods appendix on one page, it is wrong.

Validation principle: **interpretive depth** — the human gate sits at the level of
codebook structure, where a person's judgment changes the analysis, and not on
item-by-item verification, which the Vaccaro et al. meta-analysis finds actively
harmful (see `docs/METHODS.md`).
"""
