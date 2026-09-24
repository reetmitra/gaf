# 03 - His coding against his own rules (structural checks S1-S6)

The rules are the ones transcribed from his working document into `docs/CODING_RULES.md`.
A WARN is kept and flagged and is never fatal; only an ERROR fails the gate.

| check | ERROR | WARN | INFO | what it checks |
|---|---:|---:|---:|---|
| M3 | 0 | 0 | 312 |  |
| S1 | 0 | 0 | 0 | name, description, evidence present |
| S2 | 0 | 0 | 0 | every quote locates in its response |
| S3 | 0 | 10 | 0 | two-level name grammar; sub-code before new top-level |
| S4 | 0 | 0 | 0 | at most two codes on one piece of text |
| S5 | 0 | 3 | 0 | the usual two to twelve codes per response |

**RESULT: PASS - no ERROR finding.**

## Findings other than S1

| check | severity | marker | subject | message | n |
|---|---|---|---|---|---:|
| M3 | INFO | fit_ok | AI-autonomy | Fit of 'AI-autonomy' to its quote in response 100 is 0.467 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | AI-autonomy | Fit of 'AI-autonomy' to its quote in response 67 is 0.368 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | AI-machine_communication | Fit of 'AI-machine_communication' to its quote in response 42 is 0.710 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | AI-machine_communication | Fit of 'AI-machine_communication' to its quote in response 67 is 0.697 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | AI-omnipotence | Fit of 'AI-omnipotence' to its quote in response 96 is 0.506 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | AI-self-modification | Fit of 'AI-self-modification' to its quote in response 67 is 0.175 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | AI-speed | Fit of 'AI-speed' to its quote in response 67 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | AI-speed | Fit of 'AI-speed' to its quote in response 96 is 0.352 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | AI-superintelligence | Fit of 'AI-superintelligence' to its quote in response 67 is 0.221 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | AI-superintelligence | Fit of 'AI-superintelligence' to its quote in response 67 is 0.518 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | AI-superintelligence | Fit of 'AI-superintelligence' to its quote in response 67 is 0.584 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | AI-surveillance | Fit of 'AI-surveillance' to its quote in response 96 is 0.923 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | AI-tool | Fit of 'AI-tool' to its quote in response 33 is 0.703 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | adoption-high | Fit of 'adoption-high' to its quote in response 138 is 0.139 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | adoption-high | Fit of 'adoption-high' to its quote in response 236 is 0.161 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | adoption-high | Fit of 'adoption-high' to its quote in response 51 is 0.180 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | adoption-high | Fit of 'adoption-high' to its quote in response 53 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | adoption-high | Fit of 'adoption-high' to its quote in response 61 is 0.139 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | adoption-high | Fit of 'adoption-high' to its quote in response 82 is 0.414 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | adoption-necessity | Fit of 'adoption-necessity' to its quote in response 42 is 0.475 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | adoption-necessity | Fit of 'adoption-necessity' to its quote in response 64 is 0.123 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | adoption-necessity | Fit of 'adoption-necessity' to its quote in response 64 is 0.320 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | adoption-present | Fit of 'adoption-present' to its quote in response 138 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | adoption-present | Fit of 'adoption-present' to its quote in response 138 is 0.356 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | adoption-present | Fit of 'adoption-present' to its quote in response 43 is 0.290 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | adoption-present | Fit of 'adoption-present' to its quote in response 64 is 0.275 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | applications-chatbots | Fit of 'applications-chatbots' to its quote in response 11 is 0.289 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | applications-chatbots | Fit of 'applications-chatbots' to its quote in response 53 is 0.385 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-chatbots | Fit of 'applications-chatbots' to its quote in response 81 is 0.645 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-decision-making | Fit of 'applications-decision-making' to its quote in response 33 is 0.493 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-decision-making | Fit of 'applications-decision-making' to its quote in response 82 is 0.529 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-decision-making | Fit of 'applications-decision-making' to its quote in response 95 is 0.257 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | applications-deep_fakes | Fit of 'applications-deep_fakes' to its quote in response 73 is 0.612 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-financial_assistance | Fit of 'applications-financial_assistance' to its quote in response 95 is 0.620 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-financial_assistance | Fit of 'applications-financial_assistance' to its quote in response 95 is 0.788 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-friend | Fit of 'applications-friend' to its quote in response 43 is 0.120 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | applications-friend | Fit of 'applications-friend' to its quote in response 82 is 0.190 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | applications-friend | Fit of 'applications-friend' to its quote in response 82 is 0.476 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-friend | Fit of 'applications-friend' to its quote in response 84 is 0.496 (>= tau_fit 0.30). | 2 |
| M3 | INFO | fit_ok | applications-information | Fit of 'applications-information' to its quote in response 138 is 0.504 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-information | Fit of 'applications-information' to its quote in response 22 is 0.640 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-medical_care | Fit of 'applications-medical_care' to its quote in response 52 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | applications-meetings | Fit of 'applications-meetings' to its quote in response 22 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | applications-meetings | Fit of 'applications-meetings' to its quote in response 43 is 0.355 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-meetings | Fit of 'applications-meetings' to its quote in response 45 is 0.420 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-navigation | Fit of 'applications-navigation' to its quote in response 44 is 0.508 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-personal_assistant | Fit of 'applications-personal_assistant' to its quote in response 40 is 0.567 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-personal_assistant | Fit of 'applications-personal_assistant' to its quote in response 81 is 0.429 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-personal_assistant | Fit of 'applications-personal_assistant' to its quote in response 84 is 0.407 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-planning | Fit of 'applications-planning' to its quote in response 45 is 0.756 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-problem-solving | Fit of 'applications-problem-solving' to its quote in response 138 is 0.403 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-problem-solving | Fit of 'applications-problem-solving' to its quote in response 84 is 0.329 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-relationships | Fit of 'applications-relationships' to its quote in response 22 is 0.727 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-research | Fit of 'applications-research' to its quote in response 95 is 0.469 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-robotics | Fit of 'applications-robotics' to its quote in response 51 is 0.309 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-robotics | Fit of 'applications-robotics' to its quote in response 52 is 0.535 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-search | Fit of 'applications-search' to its quote in response 45 is 0.269 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | applications-search | Fit of 'applications-search' to its quote in response 80 is 0.375 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-search | Fit of 'applications-search' to its quote in response 81 is 0.295 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | applications-search | Fit of 'applications-search' to its quote in response 90 is 0.511 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-search | Fit of 'applications-search' to its quote in response 95 is 0.202 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | applications-self-driving_cars | Fit of 'applications-self-driving_cars' to its quote in response 15 is 0.304 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-self-driving_cars | Fit of 'applications-self-driving_cars' to its quote in response 19 is 0.295 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | applications-self-driving_cars | Fit of 'applications-self-driving_cars' to its quote in response 51 is 0.573 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-self-driving_cars | Fit of 'applications-self-driving_cars' to its quote in response 87 is 0.418 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-simulation | Fit of 'applications-simulation' to its quote in response 90 is 0.400 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-summarising | Fit of 'applications-summarising' to its quote in response 81 is 0.283 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | applications-summarising | Fit of 'applications-summarising' to its quote in response 90 is 0.566 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-text_generation | Fit of 'applications-text_generation' to its quote in response 45 is 0.475 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-translation | Fit of 'applications-translation' to its quote in response 44 is 0.583 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | applications-voice_recognition | Fit of 'applications-voice_recognition' to its quote in response 81 is 0.767 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | ease-life | Fit of 'ease-life' to its quote in response 23 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-life | Fit of 'ease-life' to its quote in response 40 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-life | Fit of 'ease-life' to its quote in response 43 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-life | Fit of 'ease-life' to its quote in response 51 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-life | Fit of 'ease-life' to its quote in response 53 is 0.159 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-life | Fit of 'ease-life' to its quote in response 61 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-life | Fit of 'ease-life' to its quote in response 81 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-life | Fit of 'ease-life' to its quote in response 84 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-life | Fit of 'ease-life' to its quote in response 84 is 0.120 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-life | Fit of 'ease-life' to its quote in response 90 is 0.184 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-life | Fit of 'ease-life' to its quote in response 90 is 0.526 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | ease-travel | Fit of 'ease-travel' to its quote in response 15 is 0.388 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | ease-travel | Fit of 'ease-travel' to its quote in response 19 is 0.119 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-travel | Fit of 'ease-travel' to its quote in response 44 is 0.254 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-travel | Fit of 'ease-travel' to its quote in response 53 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-work | Fit of 'ease-work' to its quote in response 11 is 0.479 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | ease-work | Fit of 'ease-work' to its quote in response 14 is 0.383 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | ease-work | Fit of 'ease-work' to its quote in response 23 is 0.403 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | ease-work | Fit of 'ease-work' to its quote in response 24 is 0.183 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-work | Fit of 'ease-work' to its quote in response 24 is 0.196 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-work | Fit of 'ease-work' to its quote in response 33 is 0.349 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | ease-work | Fit of 'ease-work' to its quote in response 43 is 0.203 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-work | Fit of 'ease-work' to its quote in response 45 is 0.150 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-work | Fit of 'ease-work' to its quote in response 45 is 0.161 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-work | Fit of 'ease-work' to its quote in response 46 is 0.391 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | ease-work | Fit of 'ease-work' to its quote in response 61 is 0.424 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | ease-work | Fit of 'ease-work' to its quote in response 81 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | ease-work | Fit of 'ease-work' to its quote in response 81 is 0.311 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | ease-work | Fit of 'ease-work' to its quote in response 81 is 0.312 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | efficiency | Fit of 'efficiency' to its quote in response 11 is 0.241 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | efficiency | Fit of 'efficiency' to its quote in response 15 is 0.148 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | efficiency | Fit of 'efficiency' to its quote in response 33 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | efficiency | Fit of 'efficiency' to its quote in response 33 is 0.094 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | efficiency | Fit of 'efficiency' to its quote in response 33 is 0.241 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | efficiency | Fit of 'efficiency' to its quote in response 45 is 0.130 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | efficiency | Fit of 'efficiency' to its quote in response 46 is 0.121 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | efficiency | Fit of 'efficiency' to its quote in response 48 is 0.066 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | efficiency | Fit of 'efficiency' to its quote in response 48 is 0.113 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | efficiency | Fit of 'efficiency' to its quote in response 73 is 0.121 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | efficiency | Fit of 'efficiency' to its quote in response 77 is 0.209 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | efficiency | Fit of 'efficiency' to its quote in response 81 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | efficiency | Fit of 'efficiency' to its quote in response 85 is 0.094 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | efficiency | Fit of 'efficiency' to its quote in response 85 is 0.241 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-hazard_avoidance | Fit of 'future-hazard_avoidance' to its quote in response 67 is 0.174 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-hazard_avoidance | Fit of 'future-hazard_avoidance' to its quote in response 73 is 0.213 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-hazard_avoidance | Fit of 'future-hazard_avoidance' to its quote in response 79 is 0.405 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | future-inevitability | Fit of 'future-inevitability' to its quote in response 138 is 0.365 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | future-inevitability | Fit of 'future-inevitability' to its quote in response 42 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-inevitability | Fit of 'future-inevitability' to its quote in response 43 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-inevitability | Fit of 'future-inevitability' to its quote in response 47 is 0.096 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-inevitability | Fit of 'future-inevitability' to its quote in response 51 is 0.085 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-inevitability | Fit of 'future-inevitability' to its quote in response 64 is 0.334 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | future-inevitability | Fit of 'future-inevitability' to its quote in response 96 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-negative | Fit of 'future-negative' to its quote in response 100 is 0.612 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | future-negative | Fit of 'future-negative' to its quote in response 73 is 0.354 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | future-negative | Fit of 'future-negative' to its quote in response 79 is 0.236 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-negative | Fit of 'future-negative' to its quote in response 96 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-positive | Fit of 'future-positive' to its quote in response 45 is 0.396 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | future-positive | Fit of 'future-positive' to its quote in response 52 is 0.350 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | future-positive | Fit of 'future-positive' to its quote in response 53 is 0.124 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-positive | Fit of 'future-positive' to its quote in response 53 is 0.229 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-positive | Fit of 'future-positive' to its quote in response 64 is 0.124 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-positive | Fit of 'future-positive' to its quote in response 84 is 0.215 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-positive | Fit of 'future-positive' to its quote in response 85 is 0.365 (>= tau_fit 0.30). | 2 |
| M3 | INFO | fit_ok | future-positive | Fit of 'future-positive' to its quote in response 88 is 0.350 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | future-positive | Fit of 'future-positive' to its quote in response 94 is 0.152 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-transformation | Fit of 'future-transformation' to its quote in response 51 is 0.378 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | future-transformation | Fit of 'future-transformation' to its quote in response 61 is 0.167 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-transformation | Fit of 'future-transformation' to its quote in response 64 is 0.167 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-transformation | Fit of 'future-transformation' to its quote in response 81 is 0.129 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-transformation | Fit of 'future-transformation' to its quote in response 82 is 0.144 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-transformation | Fit of 'future-transformation' to its quote in response 87 is 0.144 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | future-transformation | Fit of 'future-transformation' to its quote in response 90 is 0.354 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | future-transformation | Fit of 'future-transformation' to its quote in response 96 is 0.118 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | impact-climate_change | Fit of 'impact-climate_change' to its quote in response 77 is 0.503 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | impact-context-specific | Fit of 'impact-context-specific' to its quote in response 77 is 0.075 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | impact-context-specific | Fit of 'impact-context-specific' to its quote in response 79 is 0.376 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | impact-global | Fit of 'impact-global' to its quote in response 47 is 0.237 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | impact-global | Fit of 'impact-global' to its quote in response 90 is 0.335 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | impact-jobs | Fit of 'impact-jobs' to its quote in response 47 is 0.400 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | impact-jobs | Fit of 'impact-jobs' to its quote in response 51 is 0.362 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | impact-jobs | Fit of 'impact-jobs' to its quote in response 73 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | impact-jobs | Fit of 'impact-jobs' to its quote in response 73 is 0.275 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | impact-jobs | Fit of 'impact-jobs' to its quote in response 77 is 0.187 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | impact-misconception | Fit of 'impact-misconception' to its quote in response 82 is 0.439 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | impact-travel_immigration | Fit of 'impact-travel_immigration' to its quote in response 14 is 0.339 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | impact-travel_immigration | Fit of 'impact-travel_immigration' to its quote in response 15 is 0.339 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | improvement-accuracy | Fit of 'improvement-accuracy' to its quote in response 11 is 0.236 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | improvement-accuracy | Fit of 'improvement-accuracy' to its quote in response 48 is 0.316 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | improvement-accuracy | Fit of 'improvement-accuracy' to its quote in response 51 is 0.447 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | improvement-accuracy | Fit of 'improvement-accuracy' to its quote in response 73 is 0.236 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | improvement-accuracy | Fit of 'improvement-accuracy' to its quote in response 84 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | improvement-accuracy | Fit of 'improvement-accuracy' to its quote in response 85 is 0.118 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | improvement-future_readiness | Fit of 'improvement-future_readiness' to its quote in response 77 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | improvement-future_readiness | Fit of 'improvement-future_readiness' to its quote in response 85 is 0.350 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | improvement-future_readiness | Fit of 'improvement-future_readiness' to its quote in response 88 is 0.237 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | improvement-personalisation | Fit of 'improvement-personalisation' to its quote in response 33 is 0.427 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | improvement-personalisation | Fit of 'improvement-personalisation' to its quote in response 90 is 0.412 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | improvement-quality_of_life | Fit of 'improvement-quality_of_life' to its quote in response 52 is 0.391 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | improvement-quality_of_life | Fit of 'improvement-quality_of_life' to its quote in response 85 is 0.222 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | improvement-quality_of_life | Fit of 'improvement-quality_of_life' to its quote in response 88 is 0.435 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | improvement-speed | Fit of 'improvement-speed' to its quote in response 42 is 0.647 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | improvement-speed | Fit of 'improvement-speed' to its quote in response 94 is 0.408 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | improvement-speed | Fit of 'improvement-speed' to its quote in response 95 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | improvement-teaching_learning | Fit of 'improvement-teaching_learning' to its quote in response 85 is 0.554 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | jobs-businessman | Fit of 'jobs-businessman' to its quote in response 40 is 0.767 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | jobs-computer_operator | Fit of 'jobs-computer_operator' to its quote in response 40 is 0.862 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | jobs-computer_operator | Fit of 'jobs-computer_operator' to its quote in response 51 is 0.250 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | jobs-driver | Fit of 'jobs-driver' to its quote in response 19 is 0.643 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | jobs-driver | Fit of 'jobs-driver' to its quote in response 40 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | jobs-nurse | Fit of 'jobs-nurse' to its quote in response 52 is 0.793 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | jobs-surveillance | Fit of 'jobs-surveillance' to its quote in response 40 is 0.413 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | jobs-tutor | Fit of 'jobs-tutor' to its quote in response 40 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | jobs-tutor | Fit of 'jobs-tutor' to its quote in response 85 is 0.555 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | key_sectors-defence | Fit of 'key_sectors-defence' to its quote in response 33 is 0.653 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | key_sectors-disaster_management | Fit of 'key_sectors-disaster_management' to its quote in response 33 is 0.429 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | key_sectors-education | Fit of 'key_sectors-education' to its quote in response 33 is 0.368 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | key_sectors-education | Fit of 'key_sectors-education' to its quote in response 85 is 0.217 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | key_sectors-education | Fit of 'key_sectors-education' to its quote in response 96 is 0.338 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | key_sectors-elder_care | Fit of 'key_sectors-elder_care' to its quote in response 52 is 0.296 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | key_sectors-elder_care | Fit of 'key_sectors-elder_care' to its quote in response 52 is 0.439 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | key_sectors-entertainment | Fit of 'key_sectors-entertainment' to its quote in response 61 is 0.535 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | key_sectors-finance | Fit of 'key_sectors-finance' to its quote in response 95 is 0.222 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | key_sectors-health | Fit of 'key_sectors-health' to its quote in response 47 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | key_sectors-health | Fit of 'key_sectors-health' to its quote in response 88 is 0.352 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | key_sectors-health | Fit of 'key_sectors-health' to its quote in response 94 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | key_sectors-marketing | Fit of 'key_sectors-marketing' to its quote in response 14 is 0.478 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | key_sectors-technology | Fit of 'key_sectors-technology' to its quote in response 14 is 0.330 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | key_sectors-technology | Fit of 'key_sectors-technology' to its quote in response 96 is 0.338 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | key_sectors-transport | Fit of 'key_sectors-transport' to its quote in response 33 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | key_sectors-transport | Fit of 'key_sectors-transport' to its quote in response 87 is 0.205 (below tau_fit 0.30, but the judge ruled APPLIES). | 2 |
| M3 | INFO | fit_ok | negative_impacts-control | Fit of 'negative_impacts-control' to its quote in response 79 is 0.734 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-danger_to_humans | Fit of 'negative_impacts-danger_to_humans' to its quote in response 67 is 0.229 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-danger_to_humans | Fit of 'negative_impacts-danger_to_humans' to its quote in response 73 is 0.472 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-dependency | Fit of 'negative_impacts-dependency' to its quote in response 100 is 0.333 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-dependency | Fit of 'negative_impacts-dependency' to its quote in response 24 is 0.333 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-dependency | Fit of 'negative_impacts-dependency' to its quote in response 44 is 0.167 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-dependency | Fit of 'negative_impacts-dependency' to its quote in response 46 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-dependency | Fit of 'negative_impacts-dependency' to its quote in response 64 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-dependency | Fit of 'negative_impacts-dependency' to its quote in response 80 is 0.096 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-deskilling | Fit of 'negative_impacts-deskilling' to its quote in response 46 is 0.167 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-deskilling | Fit of 'negative_impacts-deskilling' to its quote in response 80 is 0.160 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-deskilling | Fit of 'negative_impacts-deskilling' to its quote in response 80 is 0.419 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-domination | Fit of 'negative_impacts-domination' to its quote in response 79 is 0.192 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-domination | Fit of 'negative_impacts-domination' to its quote in response 80 is 0.149 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-enslavement | Fit of 'negative_impacts-enslavement' to its quote in response 100 is 0.378 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-enslavement | Fit of 'negative_impacts-enslavement' to its quote in response 46 is 0.342 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-enslavement | Fit of 'negative_impacts-enslavement' to its quote in response 67 is 0.378 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-general | Fit of 'negative_impacts-general' to its quote in response 46 is 0.535 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-general | Fit of 'negative_impacts-general' to its quote in response 61 is 0.154 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-general | Fit of 'negative_impacts-general' to its quote in response 73 is 0.134 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-general | Fit of 'negative_impacts-general' to its quote in response 79 is 0.189 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-general | Fit of 'negative_impacts-general' to its quote in response 79 is 0.309 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-immobility | Fit of 'negative_impacts-immobility' to its quote in response 80 is 0.548 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-immobility | Fit of 'negative_impacts-immobility' to its quote in response 96 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-job_destruction | Fit of 'negative_impacts-job_destruction' to its quote in response 47 is 0.144 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-job_destruction | Fit of 'negative_impacts-job_destruction' to its quote in response 48 is 0.155 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-job_destruction | Fit of 'negative_impacts-job_destruction' to its quote in response 51 is 0.323 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-job_destruction | Fit of 'negative_impacts-job_destruction' to its quote in response 64 is 0.322 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-job_destruction | Fit of 'negative_impacts-job_destruction' to its quote in response 73 is 0.134 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-job_destruction | Fit of 'negative_impacts-job_destruction' to its quote in response 77 is 0.295 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-job_destruction | Fit of 'negative_impacts-job_destruction' to its quote in response 87 is 0.203 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-lack_of_inclusion | Fit of 'negative_impacts-lack_of_inclusion' to its quote in response 77 is 0.335 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-lack_of_information | Fit of 'negative_impacts-lack_of_information' to its quote in response 100 is 0.341 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-lack_of_information | Fit of 'negative_impacts-lack_of_information' to its quote in response 80 is 0.594 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-laziness | Fit of 'negative_impacts-laziness' to its quote in response 24 is 0.135 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-laziness | Fit of 'negative_impacts-laziness' to its quote in response 24 is 0.456 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-laziness | Fit of 'negative_impacts-laziness' to its quote in response 61 is 0.270 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | negative_impacts-misuse | Fit of 'negative_impacts-misuse' to its quote in response 11 is 0.544 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | negative_impacts-misuse | Fit of 'negative_impacts-misuse' to its quote in response 79 is 0.447 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-automation | Fit of 'positive_impacts-automation' to its quote in response 51 is 0.134 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-automation | Fit of 'positive_impacts-automation' to its quote in response 53 is 0.120 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-automation | Fit of 'positive_impacts-automation' to its quote in response 81 is 0.327 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-autonomy | Fit of 'positive_impacts-autonomy' to its quote in response 48 is 0.500 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-corruption_reduction | Fit of 'positive_impacts-corruption_reduction' to its quote in response 48 is 0.411 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-cost_reduction | Fit of 'positive_impacts-cost_reduction' to its quote in response 42 is 0.348 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-cost_reduction | Fit of 'positive_impacts-cost_reduction' to its quote in response 88 is 0.335 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-drug_discovery | Fit of 'positive_impacts-drug_discovery' to its quote in response 94 is 0.555 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-general | Fit of 'positive_impacts-general' to its quote in response 11 is 0.221 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-general | Fit of 'positive_impacts-general' to its quote in response 46 is 0.344 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-general | Fit of 'positive_impacts-general' to its quote in response 46 is 0.365 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-general | Fit of 'positive_impacts-general' to its quote in response 61 is 0.243 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-general | Fit of 'positive_impacts-general' to its quote in response 64 is 0.099 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-general | Fit of 'positive_impacts-general' to its quote in response 73 is 0.238 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-general | Fit of 'positive_impacts-general' to its quote in response 73 is 0.243 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-general | Fit of 'positive_impacts-general' to its quote in response 73 is 0.281 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-general | Fit of 'positive_impacts-general' to its quote in response 73 is 0.298 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-general | Fit of 'positive_impacts-general' to its quote in response 79 is 0.281 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-general | Fit of 'positive_impacts-general' to its quote in response 85 is 0.099 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-general | Fit of 'positive_impacts-general' to its quote in response 88 is 0.620 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-greater_enjoyment | Fit of 'positive_impacts-greater_enjoyment' to its quote in response 15 is 0.365 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-health | Fit of 'positive_impacts-health' to its quote in response 88 is 0.352 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-health | Fit of 'positive_impacts-health' to its quote in response 94 is 0.169 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-invention | Fit of 'positive_impacts-invention' to its quote in response 87 is 0.303 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-invention | Fit of 'positive_impacts-invention' to its quote in response 94 is 0.298 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-jobs | Fit of 'positive_impacts-jobs' to its quote in response 42 is 0.420 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-jobs | Fit of 'positive_impacts-jobs' to its quote in response 64 is 0.290 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-jobs | Fit of 'positive_impacts-jobs' to its quote in response 87 is 0.329 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-personalisation | Fit of 'positive_impacts-personalisation' to its quote in response 81 is 0.246 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-personalisation | Fit of 'positive_impacts-personalisation' to its quote in response 94 is 0.135 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-personalisation | Fit of 'positive_impacts-personalisation' to its quote in response 95 is 0.123 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-problem-solving | Fit of 'positive_impacts-problem-solving' to its quote in response 11 is 0.352 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-problem-solving | Fit of 'positive_impacts-problem-solving' to its quote in response 11 is 0.416 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-problem-solving | Fit of 'positive_impacts-problem-solving' to its quote in response 33 is 0.406 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-problem-solving | Fit of 'positive_impacts-problem-solving' to its quote in response 81 is 0.337 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-problem-solving | Fit of 'positive_impacts-problem-solving' to its quote in response 82 is 0.000 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-problem-solving | Fit of 'positive_impacts-problem-solving' to its quote in response 82 is 0.238 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-problem-solving | Fit of 'positive_impacts-problem-solving' to its quote in response 87 is 0.102 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-problem-solving | Fit of 'positive_impacts-problem-solving' to its quote in response 88 is 0.249 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-problem-solving | Fit of 'positive_impacts-problem-solving' to its quote in response 88 is 0.368 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-problem-solving | Fit of 'positive_impacts-problem-solving' to its quote in response 90 is 0.310 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-problem-solving | Fit of 'positive_impacts-problem-solving' to its quote in response 94 is 0.168 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-productivity | Fit of 'positive_impacts-productivity' to its quote in response 11 is 0.149 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-productivity | Fit of 'positive_impacts-productivity' to its quote in response 138 is 0.197 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-productivity | Fit of 'positive_impacts-productivity' to its quote in response 77 is 0.183 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | positive_impacts-productivity | Fit of 'positive_impacts-productivity' to its quote in response 77 is 0.390 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-stress_reduction | Fit of 'positive_impacts-stress_reduction' to its quote in response 24 is 0.338 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-stress_reduction | Fit of 'positive_impacts-stress_reduction' to its quote in response 52 is 0.365 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | positive_impacts-upskilling | Fit of 'positive_impacts-upskilling' to its quote in response 138 is 0.436 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | progress-economy | Fit of 'progress-economy' to its quote in response 33 is 0.786 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | progress-holistic | Fit of 'progress-holistic' to its quote in response 24 is 0.596 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | progress-holistic | Fit of 'progress-holistic' to its quote in response 33 is 0.149 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | progress-holistic | Fit of 'progress-holistic' to its quote in response 43 is 0.320 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | progress-now | Fit of 'progress-now' to its quote in response 33 is 0.231 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | progress-now | Fit of 'progress-now' to its quote in response 40 is 0.352 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | requirements-basic_income | Fit of 'requirements-basic_income' to its quote in response 47 is 0.682 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | requirements-oversight | Fit of 'requirements-oversight' to its quote in response 19 is 0.160 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | requirements-oversight | Fit of 'requirements-oversight' to its quote in response 48 is 0.288 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | requirements-oversight | Fit of 'requirements-oversight' to its quote in response 79 is 0.320 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | requirements-regulation | Fit of 'requirements-regulation' to its quote in response 46 is 0.427 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | requirements-regulation | Fit of 'requirements-regulation' to its quote in response 73 is 0.381 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | requirements-regulation | Fit of 'requirements-regulation' to its quote in response 73 is 0.565 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | safety-cybersecurity | Fit of 'safety-cybersecurity' to its quote in response 14 is 0.606 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | safety-cybersecurity | Fit of 'safety-cybersecurity' to its quote in response 81 is 0.429 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | safety-home | Fit of 'safety-home' to its quote in response 52 is 0.658 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | safety-privacy | Fit of 'safety-privacy' to its quote in response 81 is 0.494 (>= tau_fit 0.30). | 1 |
| M3 | INFO | fit_ok | safety-travel | Fit of 'safety-travel' to its quote in response 19 is 0.218 (below tau_fit 0.30, but the judge ruled APPLIES). | 1 |
| M3 | INFO | fit_ok | safety-women | Fit of 'safety-women' to its quote in response 14 is 0.810 (>= tau_fit 0.30). | 1 |
| S3 | WARN | sub_code_first | efficiency | The family 'efficiency' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 10 |
| S5 | WARN | too_few_codes | 236 | Coder 'spreadsheet' produced 1 codes for this response, fewer than the usual 2 to 12. | 1 |
| S5 | WARN | too_many_codes | 33 | Coder 'spreadsheet' produced 13 codes for this response, more than the usual 2 to 12. | 1 |
| S5 | WARN | too_many_codes | 81 | Coder 'spreadsheet' produced 14 codes for this response, more than the usual 2 to 12. | 1 |
