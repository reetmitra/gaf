# 08 - The machine run (offline stand-in coder), run id `state`

20 responses, 170 segments, 224 assignments, 18 codes in 6 families; embedding space `lexical-v1-512`; offline: True.

**Caveats the run printed about itself:**

- Offline run: M3's code-to-evidence fit does not discriminate in the lexical fallback space (median fit 0.000) and M2's grey zone is empty, so the fit and routing statistics are artefacts of the stand-in embedder rather than findings about the coding. See ADR-0019.

The two most-used machine codes account for 141 of 224 assignments: `adoption-social_change` 72, `future-imagined_scenario` 69. That is the keyword table's fallback behaviour, not a finding.

## Findings by check

| check | ERROR | WARN | INFO |
|---|---:|---:|---:|
| M1 | 0 | 7 | 86 |
| M2 | 0 | 0 | 97 |
| M3 | 0 | 0 | 224 |
| S2 | 5 | 0 | 5 |

## Findings by marker

| check | severity | marker | n |
|---|---|---|---:|
| M1 | INFO | coders_agree | 86 |
| M1 | WARN | coder_unmatched | 3 |
| M1 | WARN | coders_dispute | 4 |
| M2 | INFO | route_create | 18 |
| M2 | INFO | route_merge | 79 |
| M3 | INFO | fit_ok | 224 |
| S2 | ERROR | no_verified_evidence | 5 |
| S2 | INFO | quote_unverified | 5 |

## Every ERROR and WARN (subject is the candidate or response concerned)

| check | severity | marker | subject | message | n |
|---|---|---|---|---|---:|
| M1 | WARN | coder_unmatched | (unmatched)<->applications-education | Coder B proposed 'applications-education' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | adoption-social_change<->(unmatched) | Coder A proposed 'adoption-social_change' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | future-imagined_scenario<->(unmatched) | Coder A proposed 'future-imagined_scenario' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coders_dispute | applications-automation<->positive_impacts-problem_solving | Coders dispute: 'applications-automation' and 'positive_impacts-problem_solving' match at only cosine 0.077 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | applications-healthcare<->negative_impacts-dependence | Coders dispute: 'applications-healthcare' and 'negative_impacts-dependence' match at only cosine 0.111 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | future-imagined_scenario<->adoption-social_change | Coders dispute: 'future-imagined_scenario' and 'adoption-social_change' match at only cosine 0.000 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | positive_impacts-problem_solving<->negative_impacts-dependence | Coders dispute: 'positive_impacts-problem_solving' and 'negative_impacts-dependence' match at only cosine 0.244 (< tau_low 0.45). | 1 |
| S2 | ERROR | no_verified_evidence | future-superintelligence | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 5 |

## Pipeline counts

| quantity | value |
|---|---|
| candidates proposed (coder A / B) | 92 / 96 |
| candidates accepted | 97 |
| dropped: structural / fit / dispute | 5 / 0 / 0 |
| routes CREATE / MERGE / JUDGE | 18 / 79 / 0 |
| coder agreement rate | 0.922 |
| model calls (all mock) | 256 |
| checkpoint due | True (new codes this batch 18 > 8) |
| snapshots | snap-8c8e1bb384bd3da4, snap-26803fe832a6acdd, snap-48ba32b436a759b1 |

## The machine codebook (names and descriptions; the quotes stay in the run directory)

| code | parent | description | evidence | assignments | created in |
|---|---|---|---:|---:|---|
| `adoption-everyday_life` | - | AI becomes an unremarkable part of ordinary daily life. | 1 | 1 | snap-26803fe832a6acdd |
| `adoption-social_change` | - | AI is expected to reshape how society at large operates. | 72 | 72 | snap-8c8e1bb384bd3da4 |
| `applications-automation` | - | Physical or clerical work is carried out by machines instead of by people. | 13 | 13 | snap-8c8e1bb384bd3da4 |
| `applications-data_driven_systems` | - | Systems that learn from accumulated data direct everyday decisions. | 9 | 9 | snap-8c8e1bb384bd3da4 |
| `applications-education` | - | AI changes how teaching and learning are delivered. | 5 | 5 | snap-8c8e1bb384bd3da4 |
| `applications-healthcare` | - | AI is applied to diagnosis, treatment or access to medical care. | 10 | 10 | snap-8c8e1bb384bd3da4 |
| `applications-industry_and_transport` | - | AI is deployed across industry, agriculture, transport and infrastructure. | 6 | 6 | snap-8c8e1bb384bd3da4 |
| `future-imagined_scenario` | - | The respondent sketches a specific scenario for the years up to 2050. | 69 | 69 | snap-8c8e1bb384bd3da4 |
| `future-inevitability` | - | AI's arrival is treated as unavoidable rather than as chosen. | 4 | 4 | snap-8c8e1bb384bd3da4 |
| `future-superintelligence` | - | AI's capability comes to exceed human capability in general. | 1 | 1 | snap-26803fe832a6acdd |
| `future-uncertainty` | - | What AI will do next is treated as genuinely unknown. | 5 | 5 | snap-8c8e1bb384bd3da4 |
| `governance-responsible_development` | - | AI needs deliberate rules, ethics or oversight if it is to be used well. | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `negative_impacts-dependence` | - | People lose the ability, or the habit, of working without the system. | 9 | 9 | snap-8c8e1bb384bd3da4 |
| `negative_impacts-inequality` | - | The gains and the losses from AI fall unevenly across groups. | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `negative_impacts-job_loss` | - | Existing categories of paid work disappear as AI replaces human labour. | 6 | 6 | snap-8c8e1bb384bd3da4 |
| `negative_impacts-unskilled_workers` | - | Workers without formal skills or education carry the cost of automation. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `positive_impacts-access` | - | AI extends services to people who cannot reach them today. | 1 | 1 | snap-26803fe832a6acdd |
| `positive_impacts-problem_solving` | - | AI solves problems respondents believe people cannot solve alone. | 8 | 8 | snap-8c8e1bb384bd3da4 |
