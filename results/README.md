# Results

Each directory here is one run of the pipeline on real inputs, exported as Markdown by
`make results` (see `scripts/export_results.py`). The exporter writes counts, code names,
response numbers, metrics, cluster structure and threshold curves; it never writes a
segment, a quote or a response body, and it re-reads its own output against every text it
was told to withhold before letting it stand. The run directories themselves, which hold
the coded corpus verbatim, are gitignored and stay on the researcher's machine.

| directory | sample | question | human coding | what it is |
|---|---|---|---|---|
| [`india-process-1-20/`](india-process-1-20/README.md) | India *Process*, responses 1–20 | v2, "from now to 2050, what impacts" | yes — the PI's 342-highlight export, 147 placed | the meeting document: his coding against his rules, clustering, agreement, calibration |
| [`india-state-1-20/`](india-state-1-20/README.md) | India *State*, responses 1–20 | v3, "in 2050, what kind of roles" | none | the offline stand-in coder on the State sample, re-run under its own question |

Read each directory's `README.md` first; the numbered files behind it are the tables.
