"""The blackboard: one SQLite database holding every artefact the pipeline produces.

The predecessor design lost context across an agent chain because state lived in the
prose passed between agents. Here all state lives in one store, every model call is
stateless and re-grounds from it, and handoffs carry ids rather than prose.

Validation principle: **transparency** — a finding, a code, a merge, a judge ruling, a
dropped quote are each a row with an id, a timestamp, a snapshot reference and the
inputs that produced it.
"""
