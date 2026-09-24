# 12 - Affinity: themes that cut across the families

Affinity clusters **leaf codes**, deliberately across families rather than within
one, because the interesting case is a leaf that belongs with a leaf from somewhere
else in the tree. Groups that span families are flagged in the first column of every
table below.

## Affinity in his coding

Space `lexical-v1-512`; blend alpha 0.7 (embedding) against co-occurrence;
cut at similarity 0.5. 68 of 117 leaves were in the
matrix; 49 were not, and 64 clustered with nothing.

**1 of 2 affinity group(s) span more than one family.**
Those are the ones worth reading first: a group that stays inside a family mostly
restates the family, while a group that crosses one is the codebook telling you two
branches are doing the same work.

| spans families | families | size | responses | mechanical label | members |
|---|---|---:|---:|---|---|
| **yes** | `negative_impacts`, `positive_impacts` | 2 | 8 | `general_impacts_negative` | `negative_impacts-general`, `positive_impacts-general` |
| no | `key_sectors` | 2 | 4 | `key_sectors_education` | `key_sectors-education`, `key_sectors-technology` |

The label is mechanical — the commonest tokens among the members' names. Naming a
theme is a human act and this table does not do it.

### The same sub-label under more than one family (10)

A structural fact about the codebook rather than a clustering result: these are
sub-labels spelled identically under two or more families.

| sub-label | families | codes |
|---|---|---|
| `autonomy` | `AI`, `positive_impacts` | `AI-autonomy`, `positive_impacts-autonomy` |
| `decision-making` | `applications`, `improvement` | `applications-decision-making`, `improvement-decision-making` |
| `general` | `negative_impacts`, `positive_impacts` | `negative_impacts-general`, `positive_impacts-general` |
| `health` | `improvement`, `key_sectors`, `positive_impacts` | `improvement-health`, `key_sectors-health`, `positive_impacts-health` |
| `jobs` | `impact`, `positive_impacts` | `impact-jobs`, `positive_impacts-jobs` |
| `personalisation` | `improvement`, `positive_impacts` | `improvement-personalisation`, `positive_impacts-personalisation` |
| `problem-solving` | `applications`, `positive_impacts` | `applications-problem-solving`, `positive_impacts-problem-solving` |
| `speed` | `AI`, `improvement` | `AI-speed`, `improvement-speed` |
| `surveillance` | `AI`, `jobs` | `AI-surveillance`, `jobs-surveillance` |
| `travel` | `ease`, `safety` | `ease-travel`, `safety-travel` |

> **The analysis's own caveat.** Offline similarity describes the fallback lexical embedder, not meaning (ADR-0019): the cosine component of the blend is lexical overlap here, and a cluster is a starting point for a human read, not a semantic claim.

## Affinity in the machine run

Space `lexical-v1-512`; blend alpha 0.7 (embedding) against co-occurrence;
cut at similarity 0.5. 20 of 22 leaves were in the
matrix; 2 were not, and 20 clustered with nothing.

**No two leaves clustered together at all**, so there is nothing here that spans a
family. A vocabulary this small, in a lexical space, gives the blend nothing to
work with.

### The same sub-label under more than one family (0)

A structural fact about the codebook rather than a clustering result: these are
sub-labels spelled identically under two or more families.

None.

> **The analysis's own caveat.** Offline similarity describes the fallback lexical embedder, not meaning (ADR-0019): the cosine component of the blend is lexical overlap here, and a cluster is a starting point for a human read, not a semantic claim.
