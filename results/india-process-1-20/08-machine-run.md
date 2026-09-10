# 08 - The machine run (offline stand-in coder), run id `corpus`

20 responses, 154 segments, 197 assignments, 18 codes in 5 families; embedding space `lexical-v1-512`; offline: True.

**Caveats the run printed about itself:**

- Offline run: M3's code-to-evidence fit does not discriminate in the lexical fallback space (median fit 0.000) and M2's grey zone is empty, so the fit and routing statistics are artefacts of the stand-in embedder rather than findings about the coding. See ADR-0019.

The two most-used machine codes account for 134 of 197 assignments: `future-imagined_scenario` 68, `adoption-social_change` 66. That is the keyword table's fallback behaviour, not a finding.

## Findings by check

| check | ERROR | WARN | INFO |
|---|---:|---:|---:|
| M1 | 0 | 9 | 74 |
| M2 | 0 | 1 | 84 |
| M3 | 0 | 0 | 197 |
| S2 | 2 | 0 | 2 |

## Findings by marker

| check | severity | marker | n |
|---|---|---|---:|
| M1 | INFO | coders_agree | 74 |
| M1 | WARN | coder_unmatched | 7 |
| M1 | WARN | coders_dispute | 2 |
| M2 | INFO | route_create | 17 |
| M2 | INFO | route_merge | 67 |
| M2 | WARN | route_judge | 1 |
| M3 | INFO | fit_ok | 197 |
| S2 | ERROR | no_verified_evidence | 2 |
| S2 | INFO | quote_unverified | 2 |

## Every ERROR and WARN (subject is the candidate or response concerned)

| check | severity | marker | subject | message | n |
|---|---|---|---|---|---:|
| M1 | WARN | coder_unmatched | (unmatched)<->adoption-social_change | Coder B proposed 'adoption-social_change' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->future-imagined_scenario | Coder B proposed 'future-imagined_scenario' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | adoption-social_change<->(unmatched) | Coder A proposed 'adoption-social_change' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | future-imagined_scenario<->(unmatched) | Coder A proposed 'future-imagined_scenario' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coders_dispute | future-imagined_scenario<->adoption-social_change | Coders dispute: 'future-imagined_scenario' and 'adoption-social_change' match at only cosine 0.000 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | positive_impacts-job_creation<->adoption-everyday_life | Coders dispute: 'positive_impacts-job_creation' and 'adoption-everyday_life' match at only cosine 0.084 (< tau_low 0.45). | 1 |
| M2 | WARN | route_judge | negative_impacts-job_loss | Routes JUDGE against 'positive_impacts-job_creation' at cosine 0.462, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| S2 | ERROR | no_verified_evidence | future-superintelligence | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 2 |

## Pipeline counts

| quantity | value |
|---|---|
| candidates proposed (coder A / B) | 79 / 82 |
| candidates accepted | 85 |
| dropped: structural / fit / dispute | 2 / 0 / 0 |
| routes CREATE / MERGE / JUDGE | 17 / 67 / 1 |
| coder agreement rate | 0.902 |
| model calls (all mock) | 234 |
| checkpoint due | True (new codes this batch 18 > 8) |
| snapshots | snap-8c8e1bb384bd3da4, snap-7d52bd2c31d4b40c, snap-5ef095ea444326d7 |

## The machine codebook (names and descriptions; the quotes stay in the run directory)

| code | parent | description | evidence | assignments | created in |
|---|---|---|---:|---:|---|
| `adoption-everyday_life` | - | AI becomes an unremarkable part of ordinary daily life. | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `adoption-social_change` | - | AI is expected to reshape how society at large operates. | 66 | 66 | snap-8c8e1bb384bd3da4 |
| `applications-automation` | - | Physical or clerical work is carried out by machines instead of by people. | 8 | 8 | snap-8c8e1bb384bd3da4 |
| `applications-data_driven_systems` | - | Systems that learn from accumulated data direct everyday decisions. | 4 | 4 | snap-8c8e1bb384bd3da4 |
| `applications-education` | - | AI changes how teaching and learning are delivered. | 5 | 5 | snap-8c8e1bb384bd3da4 |
| `applications-healthcare` | - | AI is applied to diagnosis, treatment or access to medical care. | 3 | 3 | snap-7d52bd2c31d4b40c |
| `applications-industry_and_transport` | - | AI is deployed across industry, agriculture, transport and infrastructure. | 8 | 8 | snap-8c8e1bb384bd3da4 |
| `applications-personalisation` | - | Services are tailored to each individual from that person's own data. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `future-imagined_scenario` | - | The respondent sketches a specific scenario for the years up to 2050. | 68 | 68 | snap-8c8e1bb384bd3da4 |
| `future-inevitability` | - | AI's arrival is treated as unavoidable rather than as chosen. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `future-uncertainty` | - | What AI will do next is treated as genuinely unknown. | 3 | 3 | snap-7d52bd2c31d4b40c |
| `negative_impacts-dependence` | - | People lose the ability, or the habit, of working without the system. | 4 | 4 | snap-8c8e1bb384bd3da4 |
| `negative_impacts-job_loss` | - | Existing categories of paid work disappear as AI replaces human labour. | 1 | 1 | snap-7d52bd2c31d4b40c |
| `negative_impacts-surveillance` | - | Data gathered by AI systems exposes people to monitoring or misuse. | 3 | 3 | snap-8c8e1bb384bd3da4 |
| `positive_impacts-access` | - | AI extends services to people who cannot reach them today. | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `positive_impacts-job_creation` | - | New categories of paid work appear alongside the ones AI removes. | 3 | 3 | snap-8c8e1bb384bd3da4 |
| `positive_impacts-problem_solving` | - | AI solves problems respondents believe people cannot solve alone. | 12 | 12 | snap-8c8e1bb384bd3da4 |
| `positive_impacts-quality_of_life` | - | Everyday life becomes easier, safer or more comfortable. | 3 | 3 | snap-8c8e1bb384bd3da4 |
