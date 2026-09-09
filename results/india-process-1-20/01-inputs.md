# 01 - Inputs: India Process sample, responses 1-20

**Corpus.** 20 responses, source `india_process_1_20`.

> From now to 2050, what impacts do you think AI will have in shaping your society? Please answer the question by describing one specific scenario that feels most vivid and realistic to you. Please write at least 100 words, focus on one scenario only, and provide as much detail as possible.

Word counts are derived from the response bodies; the bodies themselves stay in the
gitignored run directory.

| id | number as written | note | words | highlights | distinct codes |
|---:|---|---|---:|---:|---:|
| 11 | 11 | - | 102 | 10 | 8 |
| 14 | 14 | - | 47 | 6 | 6 |
| 15 | 15 | - | 107 | 5 | 5 |
| 19 | 19 | - | 139 | 5 | 5 |
| 22 | 22 | mojibake repaired at ingest | 228 | 3 | 3 |
| 23 | 23 | - | 101 | 2 | 2 |
| 24 | 24 | - | 106 | 7 | 5 |
| 33 | 33 | - | 101 | 17 | 14 |
| 40 | 40 | - | 103 | 8 | 8 |
| 42 | 42 | - | 99 | 7 | 7 |
| 44 | 44 | - | 100 | 7 | 7 |
| 45 | 45 | - | 101 | 8 | 7 |
| 46 | 46 | - | 90 | 9 | 8 |
| 47 | 47 | - | 100 | 6 | 6 |
| 48 | 48 | - | 114 | 7 | 6 |
| 51 | 51 | - | 103 | 12 | 11 |
| 52 | 52 | - | 100 | 9 | 8 |
| 53 | 53 | - | 98 | 7 | 6 |
| 61 | 61 | - | 101 | 8 | 8 |
| 1044 | 44 | second response numbered 44 in the file | 89 | 4 | 4 |

## The coding export, placed onto the corpus

Each highlight in the principal investigator's export was located by its text in
the corpus (exact substring first, then the same fuzzy locator the S2 check uses,
threshold 0.85). Nothing was assigned by guess.

| outcome | n |
|---|---:|
| highlights in the export | 342 |
| mapped, exact | 147 |
| mapped, fuzzy | 0 |
| ambiguous (text present in more than one response) | 2 |
| unlocated (text belongs to responses not in this sample) | 193 |

Ambiguous highlights (code, and the responses the text occurs in):

| code | candidate responses |
|---|---|
| `key_sectors-defence` | 14, 33 |
| `key_sectors-education` | 14, 33 |

Best fuzzy score among the unlocated highlights: 0.41 to 0.85, all below the 0.85 line.

Mapped highlights per response: 2 to 17, every response covered.
