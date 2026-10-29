# 01 - Inputs: India Process, 39 coded responses, local models

**Corpus.** 39 responses, source `1_200`.

> *The question's wording is withheld here: at least one respondent echoed a run of 20 characters of it back in their answer, which makes the two indistinguishable to this guard. The variant is recorded on every response in the run directory and the wording is in `gaf/config.py`.*

Word counts are derived from the response bodies; the bodies themselves stay in the
gitignored run directory.

| id | number as written | note | words | highlights | distinct codes |
|---:|---|---|---:|---:|---:|
| 11 | 11 | - | 102 | 10 | 8 |
| 14 | 14 | - | 46 | 8 | 8 |
| 15 | 15 | - | 107 | 5 | 5 |
| 19 | 19 | - | 139 | 5 | 5 |
| 22 | 22 | mojibake repaired at ingest | 228 | 3 | 3 |
| 23 | 23 | - | 101 | 2 | 2 |
| 24 | 24 | - | 106 | 7 | 5 |
| 33 | 33 | - | 101 | 19 | 14 |
| 40 | 40 | - | 103 | 8 | 8 |
| 42 | 42 | - | 99 | 7 | 7 |
| 43 | 43 | - | 100 | 7 | 7 |
| 44 | 44 | - | 89 | 4 | 4 |
| 45 | 45 | - | 101 | 8 | 7 |
| 46 | 46 | - | 90 | 9 | 8 |
| 47 | 47 | - | 100 | 6 | 6 |
| 48 | 48 | - | 114 | 7 | 6 |
| 51 | 51 | - | 103 | 12 | 11 |
| 52 | 52 | - | 100 | 9 | 8 |
| 53 | 53 | - | 98 | 7 | 6 |
| 61 | 61 | - | 101 | 8 | 8 |
| 64 | 64 | - | 99 | 10 | 9 |
| 67 | 67 | - | 121 | 10 | 8 |
| 73 | 73 | - | 108 | 17 | 12 |
| 77 | 77 | - | 82 | 9 | 8 |
| 79 | 79 | - | 102 | 10 | 9 |
| 80 | 80 | - | 99 | 8 | 7 |
| 81 | 81 | - | 101 | 16 | 14 |
| 82 | 82 | - | 103 | 8 | 6 |
| 84 | 84 | - | 103 | 8 | 6 |
| 85 | 85 | - | 124 | 11 | 9 |
| 87 | 87 | - | 107 | 8 | 7 |
| 88 | 88 | - | 100 | 10 | 8 |
| 90 | 90 | - | 99 | 9 | 8 |
| 94 | 94 | - | 74 | 8 | 8 |
| 95 | 95 | - | 93 | 8 | 7 |
| 96 | 96 | - | 107 | 10 | 9 |
| 100 | 100 | - | 104 | 5 | 5 |
| 138 | 138 | - | 67 | 10 | 9 |
| 236 | 236 | - | 99 | 1 | 1 |

## The coding export, placed onto the corpus

Each highlight in the principal investigator's export was located by its text in
the corpus (exact substring first, then the same fuzzy locator the S2 check uses,
threshold 0.85). Nothing was assigned by guess.

| outcome | n |
|---|---:|
| highlights in the export | 342 |
| mapped, exact | 304 |
| mapped, fuzzy | 1 |
| mapped, resolved (ambiguous, but only one candidate is in the coded set) | 7 |
| ambiguous (text present in more than one response) | 17 |
| unlocated (text belongs to responses not in this sample) | 6 |

**Read the three mapping numbers separately: 304 exact, 1 fuzzy, 7 resolved.**
`exact` is the text found verbatim in exactly one response. `fuzzy` is the
locator's own near match above 0.85. `resolved` is a *weaker* claim than either:
the text occurs verbatim in more than one response, and exactly one of those
responses is in the coded set, so the highlight was attributed there. A single
"mapped" total of 312 would hide that distinction (ADR-0031).

**The coded set is 39 responses** of the 39 in the corpus —
every response the export places at least one highlight on. It is the universe
every number about his coding below is computed over.

Ambiguous highlights (code, and the responses the text occurs in):

| code | candidate responses |
|---|---|
| `adoption-challenges-job_losses` | 133, 171, 192, 220, 339, 357, 536, 571 |
| `adoption-challenges-privacy` | 133, 171, 192, 220, 339, 357, 536, 571 |
| `applications-decision-making` | 133, 217, 339, 357, 571 |
| `applications-medical_care` | 133, 217, 571 |
| `applications-medical_care` | 133, 217, 339, 571 |
| `efficiency` | 396, 498 |
| `future-positive` | 133, 171, 192, 339, 536, 571 |
| `future-transformation` | 133, 217, 393, 571 |
| `improvement-health` | 133, 339, 571 |
| `improvement-personalisation` | 133, 154, 158, 217, 353, 396, 490, 498, 571 |
| `improvement-quality_of_life` | 133, 171, 192, 220, 339, 536, 571 |
| `key_sectors-health` | 133, 217, 571 |
| `key_sectors-health` | 133, 171, 192, 215, 220, 339, 396, 536, 571 |
| `key_sectors-manufacturing` | 133, 171, 184, 192, 215, 220, 296, 337, 339, 357, 399, 535, 536, 571 |
| `positive_impacts-accessibility` | 133, 339, 571 |
| `positive_impacts-drug_discovery` | 133, 339, 571 |
| `positive_impacts-health` | 133, 217, 571 |

Best fuzzy score among the unlocated highlights: 0.49 to 0.75, all below the 0.85 line.

Mapped highlights per response: 1 to 19, every response covered.
