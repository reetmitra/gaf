"""Reading the PI's spreadsheets into the canonical corpus.

The survey question is absent from the source files and must be attached to every
record, because it travels with every coding call: a coder that cannot see the
question cannot code the response in context.

Validation principle: **transparency** — ingestion is a documented, replayable
transformation from a named file to content-hashed records, not a manual step.
"""
