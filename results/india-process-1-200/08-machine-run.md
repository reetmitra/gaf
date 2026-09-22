# 08 - The machine run (offline stand-in coder), run id `process200`

200 responses, 1524 segments, 1952 assignments, 22 codes in 6 families; embedding space `lexical-v1-512`; offline: True.

**Caveats the run printed about itself:**

- Offline run: M3's code-to-evidence fit does not discriminate in the lexical fallback space (median fit 0.000) and M2's grey zone is empty, so the fit and routing statistics are artefacts of the stand-in embedder rather than findings about the coding. See ADR-0019.

The two most-used machine codes account for 1281 of 1952 assignments: `future-imagined_scenario` 651, `adoption-social_change` 630. That is the keyword table's fallback behaviour, not a finding.

## Findings by check

| check | ERROR | WARN | INFO |
|---|---:|---:|---:|
| M1 | 0 | 82 | 729 |
| M2 | 0 | 2 | 846 |
| M3 | 0 | 0 | 1954 |
| S2 | 26 | 0 | 26 |

## Findings by marker

| check | severity | marker | n |
|---|---|---|---:|
| M1 | INFO | coders_agree | 729 |
| M1 | WARN | coder_unmatched | 45 |
| M1 | WARN | coders_dispute | 37 |
| M2 | INFO | route_create | 21 |
| M2 | INFO | route_merge | 825 |
| M2 | WARN | route_judge | 2 |
| M3 | INFO | fit_ok | 1954 |
| S2 | ERROR | no_verified_evidence | 26 |
| S2 | INFO | quote_unverified | 26 |

## Every ERROR and WARN (subject is the candidate or response concerned)

| check | severity | marker | subject | message | n |
|---|---|---|---|---|---:|
| M1 | WARN | coder_unmatched | (unmatched)<->adoption-everyday_life | Coder B proposed 'adoption-everyday_life' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->adoption-social_change | Coder B proposed 'adoption-social_change' and the other coder proposed nothing that could be assigned to it. | 10 |
| M1 | WARN | coder_unmatched | (unmatched)<->applications-automation | Coder B proposed 'applications-automation' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->applications-data_driven_systems | Coder B proposed 'applications-data_driven_systems' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->applications-personalisation | Coder B proposed 'applications-personalisation' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->future-imagined_scenario | Coder B proposed 'future-imagined_scenario' and the other coder proposed nothing that could be assigned to it. | 6 |
| M1 | WARN | coder_unmatched | (unmatched)<->negative_impacts-surveillance | Coder B proposed 'negative_impacts-surveillance' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->positive_impacts-problem_solving | Coder B proposed 'positive_impacts-problem_solving' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->positive_impacts-quality_of_life | Coder B proposed 'positive_impacts-quality_of_life' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | adoption-social_change<->(unmatched) | Coder A proposed 'adoption-social_change' and the other coder proposed nothing that could be assigned to it. | 6 |
| M1 | WARN | coder_unmatched | applications-automation<->(unmatched) | Coder A proposed 'applications-automation' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | applications-industry_and_transport<->(unmatched) | Coder A proposed 'applications-industry_and_transport' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | future-imagined_scenario<->(unmatched) | Coder A proposed 'future-imagined_scenario' and the other coder proposed nothing that could be assigned to it. | 11 |
| M1 | WARN | coder_unmatched | negative_impacts-job_loss<->(unmatched) | Coder A proposed 'negative_impacts-job_loss' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coders_dispute | adoption-everyday_life<->positive_impacts-problem_solving | Coders dispute: 'adoption-everyday_life' and 'positive_impacts-problem_solving' match at only cosine 0.074 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | adoption-social_change<->future-imagined_scenario | Coders dispute: 'adoption-social_change' and 'future-imagined_scenario' match at only cosine 0.000 (< tau_low 0.45). | 5 |
| M1 | WARN | coders_dispute | adoption-social_change<->governance-responsible_development | Coders dispute: 'adoption-social_change' and 'governance-responsible_development' match at only cosine 0.191 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | applications-automation<->applications-data_driven_systems | Coders dispute: 'applications-automation' and 'applications-data_driven_systems' match at only cosine 0.177 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | applications-automation<->future-imagined_scenario | Coders dispute: 'applications-automation' and 'future-imagined_scenario' match at only cosine 0.000 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | applications-automation<->negative_impacts-dependence | Coders dispute: 'applications-automation' and 'negative_impacts-dependence' match at only cosine 0.211 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | applications-data_driven_systems<->applications-automation | Coders dispute: 'applications-data_driven_systems' and 'applications-automation' match at only cosine 0.177 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | applications-data_driven_systems<->negative_impacts-surveillance | Coders dispute: 'applications-data_driven_systems' and 'negative_impacts-surveillance' match at only cosine 0.286 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | applications-data_driven_systems<->positive_impacts-problem_solving | Coders dispute: 'applications-data_driven_systems' and 'positive_impacts-problem_solving' match at only cosine 0.000 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | applications-education<->applications-industry_and_transport | Coders dispute: 'applications-education' and 'applications-industry_and_transport' match at only cosine 0.206 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | applications-healthcare<->applications-education | Coders dispute: 'applications-healthcare' and 'applications-education' match at only cosine 0.236 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | applications-healthcare<->applications-industry_and_transport | Coders dispute: 'applications-healthcare' and 'applications-industry_and_transport' match at only cosine 0.195 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | applications-industry_and_transport<->negative_impacts-job_loss | Coders dispute: 'applications-industry_and_transport' and 'negative_impacts-job_loss' match at only cosine 0.162 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | future-imagined_scenario<->adoption-social_change | Coders dispute: 'future-imagined_scenario' and 'adoption-social_change' match at only cosine 0.000 (< tau_low 0.45). | 7 |
| M1 | WARN | coders_dispute | future-imagined_scenario<->negative_impacts-surveillance | Coders dispute: 'future-imagined_scenario' and 'negative_impacts-surveillance' match at only cosine 0.000 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | governance-responsible_development<->future-superintelligence | Coders dispute: 'governance-responsible_development' and 'future-superintelligence' match at only cosine 0.183 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | governance-responsible_development<->positive_impacts-quality_of_life | Coders dispute: 'governance-responsible_development' and 'positive_impacts-quality_of_life' match at only cosine 0.091 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | negative_impacts-job_loss<->applications-data_driven_systems | Coders dispute: 'negative_impacts-job_loss' and 'applications-data_driven_systems' match at only cosine 0.078 (< tau_low 0.45). | 2 |
| M1 | WARN | coders_dispute | negative_impacts-job_loss<->positive_impacts-problem_solving | Coders dispute: 'negative_impacts-job_loss' and 'positive_impacts-problem_solving' match at only cosine 0.203 (< tau_low 0.45). | 2 |
| M1 | WARN | coders_dispute | negative_impacts-unskilled_workers<->future-imagined_scenario | Coders dispute: 'negative_impacts-unskilled_workers' and 'future-imagined_scenario' match at only cosine 0.000 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | positive_impacts-job_creation<->adoption-everyday_life | Coders dispute: 'positive_impacts-job_creation' and 'adoption-everyday_life' match at only cosine 0.084 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | positive_impacts-job_creation<->positive_impacts-problem_solving | Coders dispute: 'positive_impacts-job_creation' and 'positive_impacts-problem_solving' match at only cosine 0.271 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | positive_impacts-problem_solving<->positive_impacts-access | Coders dispute: 'positive_impacts-problem_solving' and 'positive_impacts-access' match at only cosine 0.442 (< tau_low 0.45). | 2 |
| M1 | WARN | coders_dispute | positive_impacts-quality_of_life<->future-inevitability | Coders dispute: 'positive_impacts-quality_of_life' and 'future-inevitability' match at only cosine 0.000 (< tau_low 0.45). | 1 |
| M2 | WARN | route_judge | negative_impacts-bias | Routes JUDGE against 'negative_impacts-surveillance' at cosine 0.477, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_loss | Routes JUDGE against 'positive_impacts-job_creation' at cosine 0.462, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| S2 | ERROR | no_verified_evidence | future-superintelligence | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 26 |

## Pipeline counts

| quantity | value |
|---|---|
| candidates proposed (coder A / B) | 787 / 816 |
| candidates accepted | 848 |
| dropped: structural / fit / dispute | 26 / 0 / 0 |
| routes CREATE / MERGE / JUDGE | 21 / 825 / 2 |
| coder agreement rate | 0.906 |
| model calls (all mock) | 2278 |
| checkpoint due | True (hard floor reached: 200 >= 50 responses since the last checkpoint) |
| snapshots | snap-8c8e1bb384bd3da4, snap-ac43c121915fa7a7, snap-9f247b822ac40bff, snap-6ee727e7c853a9cb, snap-e9be1126bbe516bd, snap-14e3d4a6152b1363, snap-dc610b750a1fd54e, snap-1006183c4236e8d7, snap-69c5ae799d7c3db5, snap-b50ee3f6cb914f8b, snap-911343471e874e08, snap-3694efd0025e4894, snap-c9e471babb2e9e68, snap-642244554d9bb007, snap-7164c4458ee0cf61, snap-d0712d7f8a351e82, snap-fbed9f73a1fd80d8, snap-cee7b5fee0499a5b, snap-a1984284652ff27e, snap-77628a37850fade7, snap-fb19e93adf64622e |

## The machine codebook (names and descriptions; the quotes stay in the run directory)

| code | parent | description | evidence | assignments | created in |
|---|---|---|---:|---:|---|
| `adoption-everyday_life` | - | AI becomes an unremarkable part of ordinary daily life. | 24 | 24 | snap-8c8e1bb384bd3da4 |
| `adoption-social_change` | - | AI is expected to reshape how society at large operates. | 630 | 630 | snap-8c8e1bb384bd3da4 |
| `applications-automation` | - | Physical or clerical work is carried out by machines instead of by people. | 62 | 62 | snap-8c8e1bb384bd3da4 |
| `applications-data_driven_systems` | - | Systems that learn from accumulated data direct everyday decisions. | 41 | 41 | snap-8c8e1bb384bd3da4 |
| `applications-education` | - | AI changes how teaching and learning are delivered. | 56 | 56 | snap-8c8e1bb384bd3da4 |
| `applications-healthcare` | - | AI is applied to diagnosis, treatment or access to medical care. | 86 | 86 | snap-ac43c121915fa7a7 |
| `applications-industry_and_transport` | - | AI is deployed across industry, agriculture, transport and infrastructure. | 64 | 64 | snap-8c8e1bb384bd3da4 |
| `applications-personalisation` | - | Services are tailored to each individual from that person's own data. | 9 | 9 | snap-8c8e1bb384bd3da4 |
| `future-imagined_scenario` | - | The respondent sketches a specific scenario for the years up to 2050. | 651 | 651 | snap-8c8e1bb384bd3da4 |
| `future-inevitability` | - | AI's arrival is treated as unavoidable rather than as chosen. | 13 | 13 | snap-8c8e1bb384bd3da4 |
| `future-superintelligence` | - | AI's capability comes to exceed human capability in general. | 8 | 8 | snap-9f247b822ac40bff |
| `future-uncertainty` | - | What AI will do next is treated as genuinely unknown. | 8 | 8 | snap-ac43c121915fa7a7 |
| `governance-responsible_development` | - | AI needs deliberate rules, ethics or oversight if it is to be used well. | 16 | 16 | snap-9f247b822ac40bff |
| `negative_impacts-dependence` | - | People lose the ability, or the habit, of working without the system. | 44 | 44 | snap-8c8e1bb384bd3da4 |
| `negative_impacts-inequality` | - | The gains and the losses from AI fall unevenly across groups. | 1 | 1 | snap-7164c4458ee0cf61 |
| `negative_impacts-job_loss` | - | Existing categories of paid work disappear as AI replaces human labour. | 33 | 33 | snap-ac43c121915fa7a7 |
| `negative_impacts-surveillance` | - | Data gathered by AI systems exposes people to monitoring or misuse. | 19 | 19 | snap-8c8e1bb384bd3da4 |
| `negative_impacts-unskilled_workers` | - | Workers without formal skills or education carry the cost of automation. | 1 | 1 | snap-c9e471babb2e9e68 |
| `positive_impacts-access` | - | AI extends services to people who cannot reach them today. | 11 | 11 | snap-8c8e1bb384bd3da4 |
| `positive_impacts-job_creation` | - | New categories of paid work appear alongside the ones AI removes. | 15 | 15 | snap-8c8e1bb384bd3da4 |
| `positive_impacts-problem_solving` | - | AI solves problems respondents believe people cannot solve alone. | 117 | 117 | snap-8c8e1bb384bd3da4 |
| `positive_impacts-quality_of_life` | - | Everyday life becomes easier, safer or more comfortable. | 43 | 43 | snap-8c8e1bb384bd3da4 |
