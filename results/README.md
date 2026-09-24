# Results

Each directory here is one run of the pipeline on real inputs, exported as Markdown by
`scripts/export_results.py` (`make results` for a single run, `make results-full` for the
whole sequence from the raw files). The exporter writes counts, code names, response
numbers, metrics, cluster structure, threshold curves and the handover trace; it never
writes a segment, a quote, a highlight's content, an organised codebook's example or a
response body. Before letting its output stand it re-reads **every file it wrote**, in
every subdirectory and of every type, against every text the run directories hold, and
deletes the whole export on a single shared run of characters. The run directories
themselves, which hold the coded corpus verbatim, are gitignored and stay on the
researcher's machine.

| directory | sample | question | human coding | what it is |
|---|---|---|---|---|
| [`india-process-1-200/`](india-process-1-200/README.md) | India *Process*, responses 1–200 | v2, "from now to 2050, what impacts" | yes — the PI's 342-pairing export placed on the full corpus, 312 placed over 39 responses | the current result: his codebook organised and defined, checked, clustered, compared, crosswalked; the cold machine run, a seeded run, a halted run and its resumption |
| [`india-process-1-20/`](india-process-1-20/README.md) | India *Process*, responses 1–20 | v2, "from now to 2050, what impacts" | yes — the PI's 342-highlight export, 147 placed | the 10 September meeting document, kept as the record of what was shown then |
| [`india-state-1-20/`](india-state-1-20/README.md) | India *State*, responses 1–20 | v3, "in 2050, what kind of roles" | none | the offline stand-in coder on the State sample, re-run under its own question |

Read each directory's `README.md` first; the numbered files behind it are the tables.

`india-process-1-20/` and `india-state-1-20/` are **not regenerated**. They are what the
principal investigator was shown on 10 September, and the numbers in them are the
baseline the current result is read against.

## Three things to know before quoting any number here

1. **Every run was offline.** The coders, the judge and the refactorer are deterministic
   mocks and the embedding space is the lexical fallback. The machine coder is a keyword
   table. Its agreement with an expert was never the question; whether the harness
   measures, explains and reproduces a disagreement on real inputs is.
2. **Definitions are published one at a time, or not at all.** A definition is only as
   shareable as whoever wrote it made it, and some of the researcher's own quote the
   response that prompted them. Each is tested on its own; a colliding one appears as
   its code name plus a note, never as text. The same per-item rule is applied to the
   survey question, to a line of a copied table and to a whole copied page.
3. **A file that is missing is named, not omitted.** Each directory's `README.md` lists
   what was not produced and why, including anything the guard held back.
