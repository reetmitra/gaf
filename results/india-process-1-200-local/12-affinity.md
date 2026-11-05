# 12 - Affinity: themes that cut across the families

Affinity clusters **leaf codes**, deliberately across families rather than within
one, because the interesting case is a leaf that belongs with a leaf from somewhere
else in the tree. Groups that span families are flagged in the first column of every
table below.

## Affinity in the machine run

Space `lexical-v1-512`; blend alpha 0.7 (embedding) against co-occurrence;
cut at similarity 0.5. 115 of 149 leaves were in the
matrix; 47 were not, and 115 clustered with nothing.

**No two leaves clustered together at all**, so there is nothing here that spans a
family. A vocabulary this small, in a lexical space, gives the blend nothing to
work with.

### The same sub-label under more than one family (12)

A structural fact about the codebook rather than a clustering result: these are
sub-labels spelled identically under two or more families.

| sub-label | families | codes |
|---|---|---|
| `assistance_for_disabled` | `AI`, `accessibility` | `AI-assistance_for_disabled`, `accessibility-assistance_for_disabled` |
| `dependence-lifestyle` | `AI`, `ai` | `AI-dependence-lifestyle`, `ai-dependence-lifestyle` |
| `enhanced-communication` | `AI`, `impact` | `AI-enhanced-communication`, `impact-enhanced-communication` |
| `job_transformation` | `employment_transformation`, `labor` | `employment_transformation-job_transformation`, `labor-job_transformation` |
| `multi_use` | `AI`, `ai` | `AI-multi_use`, `ai-multi_use` |
| `productivity_enhancement` | `AI`, `ai` | `AI-productivity_enhancement`, `ai-productivity_enhancement` |
| `productivity_gain` | `economic_efficiency`, `economic_impact` | `economic_efficiency-productivity_gain`, `economic_impact-productivity_gain` |
| `sector-focus-health` | `AI`, `ai` | `AI-sector-focus-health`, `ai-sector-focus-health` |
| `sector_transformation` | `AI`, `education` | `AI-sector_transformation`, `education-sector_transformation` |
| `utility` | `AI`, `ai` | `AI-utility`, `ai-utility` |
| `work_ease` | `impact`, `utility` | `impact-work_ease`, `utility-work_ease` |
| `work_relief` | `positive_outcomes`, `positive_outlook` | `positive_outcomes-work_relief`, `positive_outlook-work_relief` |

> **The analysis's own caveat.** Offline similarity describes the fallback lexical embedder, not meaning (ADR-0019): the cosine component of the blend is lexical overlap here, and a cluster is a starting point for a human read, not a semantic claim.
