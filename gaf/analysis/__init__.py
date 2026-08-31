"""The deterministic analysis tail and the validation dossier. No models run here.

Reproduces the Chan (2025) method exactly: binary occurrence matrix, low-frequency
filter, Ward's linkage, agglomeration schedule, cluster means. Adds the Alqazlan-style
concurrent validation against the human golden set, the saturation curve that
grounded theory's theoretical sampling requires, and the model-free lexical check.

Respondent metadata is joined here, and only here — never during coding.

Validation principle: **reliability** — the entire tail is a pure function of the
occurrence matrix, so a reviewer can rerun it and get the same numbers.
"""
