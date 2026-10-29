# 12 - Affinity: themes that cut across the families

Affinity clusters **leaf codes**, deliberately across families rather than within
one, because the interesting case is a leaf that belongs with a leaf from somewhere
else in the tree. Groups that span families are flagged in the first column of every
table below.

## Affinity in the machine run

Space `lexical-v1-512`; blend alpha 0.7 (embedding) against co-occurrence;
cut at similarity 0.5. 43 of 88 leaves were in the
matrix; 48 were not, and 43 clustered with nothing.

**No two leaves clustered together at all**, so there is nothing here that spans a
family. A vocabulary this small, in a lexical space, gives the blend nothing to
work with.

### The same sub-label under more than one family (3)

A structural fact about the codebook rather than a clustering result: these are
sub-labels spelled identically under two or more families.

| sub-label | families | codes |
|---|---|---|
| `misuse` | `concern`, `negative_impacts` | `concern-misuse`, `negative_impacts-misuse` |
| `productivity_enhancement` | `AI`, `ai` | `AI-productivity_enhancement`, `ai-productivity_enhancement` |
| `utility` | `AI`, `ai` | `AI-utility`, `ai-utility` |

> **The analysis's own caveat.** Offline similarity describes the fallback lexical embedder, not meaning (ADR-0019): the cosine component of the blend is lexical overlap here, and a cluster is a starting point for a human read, not a semantic claim.
