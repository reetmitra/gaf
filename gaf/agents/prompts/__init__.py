"""Versioned prompt templates, one file per role and version.

A prompt is data, and its version id is recorded with every call it produces. A change
of wording is therefore a visible event in the audit log rather than silent drift
between runs.

Three of the four templates here are resolved by `loader.py`, which is the enumerable
prompt surface of a *run*: the wording whose hash a run manifest records as having
produced a coding. `definer_v1` sits beside them but is resolved by
`gaf.agents.definer`'s own registry instead, because the Definer runs in neither loop
and never sees a response being coded — a run manifest carrying its hash would claim
that run's coding depended on wording it never read. See ADR-0034.

Validation principle: **reliability**.
"""
