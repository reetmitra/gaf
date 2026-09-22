# 06 - Concurrent validation: his coding against the machine's

The machine side here is the offline stand-in coder (a deterministic keyword table used
so the pipeline runs without a model or a key). Its agreement with an expert is not the
question; whether the harness measures and explains a disagreement on real inputs is.

## Descriptions on both sides

Embedding space `lexical-v1-512`, tau_high 0.8: 1 of 109 human codes matched to one of 20 machine codes.

| scope | precision | recall | F1 | kappa | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| all codes (union vocabulary) | 0.000 | 0.000 | 0.000 | -0.043 | 0 | 166 | 278 |
| matched codes only | 0.000 | 0.000 | 0.000 | -0.150 | 0 | 4 | 7 |

| segment level | precision | recall | F1 |
|---|---:|---:|---:|
| span-overlap weighted | 0.000 | 0.000 | 0.000 |
| strict (overlap >= 0.5) | 0.000 | 0.000 | 0.000 |

Right code, wrong place: 0; mean overlap on shared codes 0.000.

### Code matching (Hungarian assignment, nearest pairs)

| human code | machine code | similarity | accepted |
|---|---|---:|---|
| `future-inevitability` | `future-inevitability` | 1.000 | yes |
| `negative_impacts-misuse` | `negative_impacts-surveillance` | 0.503 | no |
| `negative_impacts-job_destruction` | `negative_impacts-job_loss` | 0.499 | no |
| `positive_impacts-problem-solving` | `positive_impacts-problem_solving` | 0.475 | no |
| `ease-life` | `positive_impacts-quality_of_life` | 0.470 | no |
| `improvement-teaching_learning` | `applications-education` | 0.466 | no |
| `positive_impacts-jobs` | `positive_impacts-job_creation` | 0.458 | no |
| `adoption-high` | `adoption-everyday_life` | 0.456 | no |
| `positive_impacts-personalisation` | `applications-personalisation` | 0.455 | no |
| `applications-medical_care` | `applications-healthcare` | 0.420 | no |
| `negative_impacts-laziness` | `negative_impacts-dependence` | 0.402 | no |
| `positive_impacts-autonomy` | `positive_impacts-access` | 0.402 | no |
| `AI-surveillance` | `future-superintelligence` | 0.396 | no |
| `key_sectors-transport` | `applications-industry_and_transport` | 0.361 | no |
| `progress-holistic` | `future-uncertainty` | 0.354 | no |
| `positive_impacts-automation` | `applications-automation` | 0.338 | no |
| `requirements-oversight` | `governance-responsible_development` | 0.334 | no |
| `adoption-necessity` | `adoption-social_change` | 0.286 | no |
| `improvement-personalisation` | `applications-data_driven_systems` | 0.203 | no |
| `future-positive` | `future-imagined_scenario` | 0.156 | no |

### Over-coding - machine codes with no human counterpart (19 codes, 367 segments)

| machine code | segments | responses | nearest human code | cosine |
|---|---:|---|---|---:|
| `adoption-everyday_life` | 4 | 42, 61, 82, 236 | `ease-life` | 0.470 |
| `adoption-social_change` | 118 | 11, 14, 15, 19, 22, 23, 24, 33, 40, 42, 43, 44, 45, 46, 47, 48, 51, 52, 53, 61, 64, 67, 73, 77, 79, 81, 84, 85, 87, 88, 90, 94, 95, 96, 100, 138, 236 | `adoption-necessity` | 0.286 |
| `applications-automation` | 17 | 42, 51, 53, 73, 77, 80, 82, 87, 94, 96 | `positive_impacts-automation` | 0.338 |
| `applications-data_driven_systems` | 5 | 19, 48, 138 | `positive_impacts-personalisation` | 0.228 |
| `applications-education` | 11 | 33, 40, 45, 53, 61, 84, 85, 94, 96 | `improvement-teaching_learning` | 0.466 |
| `applications-healthcare` | 5 | 47, 52, 94 | `applications-medical_care` | 0.420 |
| `applications-industry_and_transport` | 15 | 14, 15, 19, 47, 51, 87, 96 | `key_sectors-transport` | 0.361 |
| `applications-personalisation` | 2 | 33, 81 | `positive_impacts-personalisation` | 0.455 |
| `future-imagined_scenario` | 123 | 11, 14, 15, 19, 22, 23, 24, 33, 40, 42, 43, 44, 45, 46, 47, 48, 51, 52, 53, 61, 64, 67, 73, 77, 79, 80, 81, 82, 84, 85, 87, 90, 94, 95, 96, 100, 236 | `future-positive` | 0.156 |
| `future-superintelligence` | 1 | 67 | `AI-surveillance` | 0.396 |
| `future-uncertainty` | 5 | 43, 44, 84, 236 | `future-inevitability` | 0.396 |
| `governance-responsible_development` | 4 | 73, 79 | `requirements-oversight` | 0.334 |
| `negative_impacts-dependence` | 13 | 24, 44, 64, 77, 80, 87, 100, 236 | `negative_impacts-laziness` | 0.402 |
| `negative_impacts-job_loss` | 2 | 48, 96 | `negative_impacts-job_destruction` | 0.499 |
| `negative_impacts-surveillance` | 7 | 11, 19, 40, 79, 81, 96 | `negative_impacts-misuse` | 0.503 |
| `positive_impacts-access` | 2 | 14, 15 | `positive_impacts-autonomy` | 0.402 |
| `positive_impacts-job_creation` | 4 | 22, 42, 51, 77 | `positive_impacts-jobs` | 0.458 |
| `positive_impacts-problem_solving` | 24 | 11, 22, 33, 42, 45, 48, 51, 53, 67, 73, 80, 81, 84, 88, 90, 94, 138 | `positive_impacts-problem-solving` | 0.475 |
| `positive_impacts-quality_of_life` | 5 | 19, 22, 33, 90 | `ease-life` | 0.470 |

### Blind spots - human codes the machine never produced (108 codes, 305 segments)

The only place the negative example "you did not generate a new code" is observable:
a code never invented leaves no artefact inside a run. The segments themselves are in
the local run directory's `agreement.md`.

| human code | segments | responses | nearest machine code | cosine |
|---|---:|---|---|---:|
| `AI-autonomy` | 2 | 67, 100 | `negative_impacts-job_loss` | 0.249 |
| `AI-machine_communication` | 2 | 42, 67 | `positive_impacts-job_creation` | 0.211 |
| `AI-omnipotence` | 1 | 96 | `negative_impacts-job_loss` | 0.344 |
| `AI-self-modification` | 1 | 67 | `applications-industry_and_transport` | 0.287 |
| `AI-speed` | 2 | 67, 96 | `future-superintelligence` | 0.249 |
| `AI-superintelligence` | 3 | 67 | `future-superintelligence` | 0.388 |
| `AI-surveillance` | 1 | 96 | `future-superintelligence` | 0.396 |
| `AI-tool` | 1 | 33 | `future-inevitability` | 0.294 |
| `adoption-high` | 6 | 51, 53, 61, 82, 138, 236 | `adoption-everyday_life` | 0.456 |
| `adoption-necessity` | 3 | 42, 64 | `adoption-social_change` | 0.286 |
| `adoption-present` | 4 | 43, 64, 138 | `future-superintelligence` | 0.237 |
| `applications-chatbots` | 3 | 11, 53, 81 | `future-uncertainty` | 0.204 |
| `applications-decision-making` | 3 | 33, 82, 95 | `applications-data_driven_systems` | 0.190 |
| `applications-deep_fakes` | 1 | 73 | `applications-industry_and_transport` | 0.310 |
| `applications-financial_assistance` | 2 | 95 | `adoption-everyday_life` | 0.274 |
| `applications-friend` | 5 | 43, 82, 84 | `applications-education` | 0.285 |
| `applications-information` | 2 | 22, 138 | `applications-education` | 0.237 |
| `applications-medical_care` | 1 | 52 | `applications-healthcare` | 0.420 |
| `applications-meetings` | 3 | 22, 43, 45 | `applications-personalisation` | 0.252 |
| `applications-navigation` | 1 | 44 | `applications-education` | 0.267 |
| `applications-personal_assistant` | 3 | 40, 81, 84 | `future-superintelligence` | 0.341 |
| `applications-planning` | 1 | 45 | `applications-education` | 0.267 |
| `applications-problem-solving` | 2 | 84, 138 | `positive_impacts-problem_solving` | 0.274 |
| `applications-relationships` | 1 | 22 | `applications-education` | 0.270 |
| `applications-research` | 1 | 95 | `applications-education` | 0.237 |
| `applications-robotics` | 2 | 51, 52 | `applications-personalisation` | 0.342 |
| `applications-search` | 5 | 45, 80, 81, 90, 95 | `applications-education` | 0.190 |
| `applications-self-driving_cars` | 4 | 15, 19, 51, 87 | `positive_impacts-access` | 0.380 |
| `applications-simulation` | 1 | 90 | `applications-education` | 0.224 |
| `applications-summarising` | 2 | 81, 90 | `applications-education` | 0.224 |
| `applications-text_generation` | 1 | 45 | `applications-education` | 0.119 |
| `applications-translation` | 1 | 44 | `applications-personalisation` | 0.374 |
| `applications-voice_recognition` | 1 | 81 | `future-superintelligence` | 0.262 |
| `ease-life` | 11 | 23, 40, 43, 51, 53, 61, 81, 84, 90 | `positive_impacts-quality_of_life` | 0.470 |
| `ease-travel` | 4 | 15, 19, 44, 53 | `negative_impacts-job_loss` | 0.186 |
| `ease-work` | 14 | 11, 14, 23, 24, 33, 43, 45, 46, 61, 81 | `negative_impacts-job_loss` | 0.338 |
| `efficiency` | 14 | 11, 15, 33, 45, 46, 48, 73, 77, 81, 85 | `applications-education` | 0.148 |
| `future-hazard_avoidance` | 3 | 67, 73, 79 | `future-superintelligence` | 0.274 |
| `future-negative` | 4 | 73, 79, 96, 100 | `future-inevitability` | 0.289 |
| `future-positive` | 10 | 45, 52, 53, 64, 84, 85, 88, 94 | `future-inevitability` | 0.356 |
| `future-transformation` | 8 | 51, 61, 64, 81, 82, 87, 90, 96 | `positive_impacts-quality_of_life` | 0.323 |
| `impact-climate_change` | 1 | 77 | `applications-education` | 0.267 |
| `impact-context-specific` | 2 | 77, 79 | `positive_impacts-problem_solving` | 0.300 |
| `impact-global` | 2 | 47, 90 | `positive_impacts-problem_solving` | 0.311 |
| `impact-jobs` | 5 | 47, 51, 73, 77 | `negative_impacts-job_loss` | 0.351 |
| `impact-misconception` | 1 | 82 | `positive_impacts-problem_solving` | 0.213 |
| `impact-travel_immigration` | 2 | 14, 15 | `positive_impacts-problem_solving` | 0.289 |
| `improvement-accuracy` | 6 | 11, 48, 51, 73, 84, 85 | `future-uncertainty` | 0.118 |
| `improvement-future_readiness` | 3 | 77, 85, 88 | `future-inevitability` | 0.341 |
| `improvement-personalisation` | 2 | 33, 90 | `negative_impacts-surveillance` | 0.357 |
| `improvement-quality_of_life` | 3 | 52, 85, 88 | `adoption-everyday_life` | 0.429 |
| `improvement-speed` | 3 | 42, 94, 95 | `applications-healthcare` | 0.202 |
| `improvement-teaching_learning` | 1 | 85 | `applications-education` | 0.466 |
| `jobs-businessman` | 1 | 40 | `future-imagined_scenario` | 0.138 |
| `jobs-computer_operator` | 2 | 40, 51 | `adoption-everyday_life` | 0.250 |
| `jobs-driver` | 2 | 19, 40 | `positive_impacts-job_creation` | 0.186 |
| `jobs-nurse` | 1 | 52 | `applications-healthcare` | 0.261 |
| `jobs-surveillance` | 1 | 40 | `negative_impacts-surveillance` | 0.211 |
| `jobs-tutor` | 2 | 40, 85 | `applications-education` | 0.320 |
| `key_sectors-defence` | 1 | 33 | `applications-healthcare` | 0.285 |
| `key_sectors-disaster_management` | 1 | 33 | `positive_impacts-quality_of_life` | 0.145 |
| `key_sectors-education` | 3 | 33, 85, 96 | `applications-education` | 0.292 |
| `key_sectors-elder_care` | 2 | 52 | `applications-healthcare` | 0.139 |
| `key_sectors-entertainment` | 1 | 61 | `positive_impacts-quality_of_life` | 0.166 |
| `key_sectors-finance` | 1 | 95 | `adoption-everyday_life` | 0.178 |
| `key_sectors-health` | 3 | 47, 88, 94 | `applications-healthcare` | 0.305 |
| `key_sectors-marketing` | 1 | 14 | `positive_impacts-quality_of_life` | 0.158 |
| `key_sectors-technology` | 2 | 14, 96 | `applications-education` | 0.195 |
| `key_sectors-transport` | 3 | 33, 87 | `applications-industry_and_transport` | 0.361 |
| `negative_impacts-control` | 1 | 79 | `negative_impacts-surveillance` | 0.384 |
| `negative_impacts-danger_to_humans` | 2 | 67, 73 | `negative_impacts-job_loss` | 0.395 |
| `negative_impacts-dependency` | 6 | 24, 44, 46, 64, 80, 100 | `negative_impacts-job_loss` | 0.370 |
| `negative_impacts-deskilling` | 3 | 46, 80 | `negative_impacts-dependence` | 0.277 |
| `negative_impacts-domination` | 2 | 79, 80 | `negative_impacts-surveillance` | 0.302 |
| `negative_impacts-enslavement` | 3 | 46, 67, 100 | `negative_impacts-job_loss` | 0.419 |
| `negative_impacts-general` | 5 | 46, 61, 73, 79 | `negative_impacts-surveillance` | 0.322 |
| `negative_impacts-immobility` | 2 | 80, 96 | `negative_impacts-surveillance` | 0.381 |
| `negative_impacts-job_destruction` | 7 | 47, 48, 51, 64, 73, 77, 87 | `negative_impacts-job_loss` | 0.499 |
| `negative_impacts-lack_of_inclusion` | 1 | 77 | `negative_impacts-dependence` | 0.333 |
| `negative_impacts-lack_of_information` | 2 | 80, 100 | `negative_impacts-surveillance` | 0.252 |
| `negative_impacts-laziness` | 3 | 24, 61 | `negative_impacts-dependence` | 0.402 |
| `negative_impacts-misuse` | 2 | 11, 79 | `negative_impacts-surveillance` | 0.503 |
| `positive_impacts-automation` | 3 | 51, 53, 81 | `applications-automation` | 0.338 |
| `positive_impacts-autonomy` | 1 | 48 | `positive_impacts-access` | 0.402 |
| `positive_impacts-corruption_reduction` | 1 | 48 | `positive_impacts-problem_solving` | 0.222 |
| `positive_impacts-cost_reduction` | 2 | 42, 88 | `positive_impacts-access` | 0.350 |
| `positive_impacts-drug_discovery` | 1 | 94 | `negative_impacts-job_loss` | 0.308 |
| `positive_impacts-general` | 12 | 11, 46, 61, 64, 73, 79, 85, 88 | `future-superintelligence` | 0.347 |
| `positive_impacts-greater_enjoyment` | 1 | 15 | `positive_impacts-problem_solving` | 0.387 |
| `positive_impacts-health` | 2 | 88, 94 | `positive_impacts-problem_solving` | 0.335 |
| `positive_impacts-invention` | 2 | 87, 94 | `positive_impacts-job_creation` | 0.421 |
| `positive_impacts-jobs` | 3 | 42, 64, 87 | `positive_impacts-job_creation` | 0.458 |
| `positive_impacts-personalisation` | 3 | 81, 94, 95 | `applications-personalisation` | 0.455 |
| `positive_impacts-problem-solving` | 11 | 11, 33, 81, 82, 87, 88, 90, 94 | `positive_impacts-problem_solving` | 0.475 |
| `positive_impacts-productivity` | 4 | 11, 77, 138 | `positive_impacts-problem_solving` | 0.316 |
| `positive_impacts-stress_reduction` | 2 | 24, 52 | `positive_impacts-problem_solving` | 0.297 |
| `positive_impacts-upskilling` | 1 | 138 | `positive_impacts-problem_solving` | 0.370 |
| `progress-economy` | 1 | 33 | `adoption-everyday_life` | 0.250 |
| `progress-holistic` | 3 | 24, 33, 43 | `adoption-everyday_life` | 0.373 |
| `progress-now` | 2 | 33, 40 | `adoption-everyday_life` | 0.157 |
| `requirements-basic_income` | 1 | 47 | `positive_impacts-quality_of_life` | 0.175 |
| `requirements-oversight` | 3 | 19, 48, 79 | `future-superintelligence` | 0.337 |
| `requirements-regulation` | 3 | 46, 73 | `governance-responsible_development` | 0.288 |
| `safety-cybersecurity` | 2 | 14, 81 | `future-uncertainty` | 0.113 |
| `safety-home` | 1 | 52 | `applications-education` | 0.126 |
| `safety-privacy` | 1 | 81 | `applications-education` | 0.146 |
| `safety-travel` | 1 | 19 | `applications-healthcare` | 0.252 |
| `safety-women` | 1 | 14 | `future-superintelligence` | 0.205 |

## Name against name: no descriptions on either side

Embedding space `lexical-v1-512`, tau_high 0.8: 3 of 109 human codes matched to one of 20 machine codes.

| scope | precision | recall | F1 | kappa | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| all codes (union vocabulary) | 0.042 | 0.025 | 0.032 | -0.011 | 7 | 159 | 271 |
| matched codes only | 0.280 | 0.389 | 0.326 | 0.179 | 7 | 18 | 11 |

| segment level | precision | recall | F1 |
|---|---:|---:|---:|
| span-overlap weighted | 0.011 | 0.013 | 0.012 |
| strict (overlap >= 0.5) | 0.016 | 0.019 | 0.018 |

Right code, wrong place: 5; mean overlap on shared codes 0.379.

### Code matching (Hungarian assignment, nearest pairs)

| human code | machine code | similarity | accepted |
|---|---|---:|---|
| `future-inevitability` | `future-inevitability` | 1.000 | yes |
| `positive_impacts-problem-solving` | `positive_impacts-problem_solving` | 1.000 | yes |
| `positive_impacts-jobs` | `positive_impacts-job_creation` | 0.866 | yes |
| `negative_impacts-job_destruction` | `negative_impacts-job_loss` | 0.750 | no |
| `impact-travel_immigration` | `positive_impacts-access` | 0.667 | no |
| `negative_impacts-control` | `negative_impacts-dependence` | 0.667 | no |
| `negative_impacts-dependency` | `negative_impacts-surveillance` | 0.667 | no |
| `improvement-quality_of_life` | `positive_impacts-quality_of_life` | 0.577 | no |
| `AI-superintelligence` | `future-superintelligence` | 0.500 | no |
| `applications-chatbots` | `applications-automation` | 0.500 | no |
| `applications-information` | `applications-education` | 0.500 | no |
| `applications-meetings` | `applications-healthcare` | 0.500 | no |
| `applications-planning` | `applications-personalisation` | 0.500 | no |
| `future-positive` | `future-uncertainty` | 0.500 | no |
| `adoption-high` | `adoption-everyday_life` | 0.408 | no |
| `adoption-necessity` | `adoption-social_change` | 0.408 | no |
| `applications-navigation` | `applications-industry_and_transport` | 0.408 | no |
| `future-negative` | `future-imagined_scenario` | 0.408 | no |
| `jobs-nurse` | `governance-responsible_development` | 0.408 | no |
| `applications-friend` | `applications-data_driven_systems` | 0.354 | no |

### Over-coding - machine codes with no human counterpart (17 codes, 339 segments)

| machine code | segments | responses | nearest human code | cosine |
|---|---:|---|---|---:|
| `adoption-everyday_life` | 4 | 42, 61, 82, 236 | `adoption-high` | 0.408 |
| `adoption-social_change` | 118 | 11, 14, 15, 19, 22, 23, 24, 33, 40, 42, 43, 44, 45, 46, 47, 48, 51, 52, 53, 61, 64, 67, 73, 77, 79, 81, 84, 85, 87, 88, 90, 94, 95, 96, 100, 138, 236 | `adoption-high` | 0.408 |
| `applications-automation` | 17 | 42, 51, 53, 73, 77, 80, 82, 87, 94, 96 | `applications-chatbots` | 0.500 |
| `applications-data_driven_systems` | 5 | 19, 48, 138 | `applications-chatbots` | 0.354 |
| `applications-education` | 11 | 33, 40, 45, 53, 61, 84, 85, 94, 96 | `applications-chatbots` | 0.500 |
| `applications-healthcare` | 5 | 47, 52, 94 | `applications-chatbots` | 0.500 |
| `applications-industry_and_transport` | 15 | 14, 15, 19, 47, 51, 87, 96 | `applications-chatbots` | 0.408 |
| `applications-personalisation` | 2 | 33, 81 | `applications-chatbots` | 0.500 |
| `future-imagined_scenario` | 123 | 11, 14, 15, 19, 22, 23, 24, 33, 40, 42, 43, 44, 45, 46, 47, 48, 51, 52, 53, 61, 64, 67, 73, 77, 79, 80, 81, 82, 84, 85, 87, 90, 94, 95, 96, 100, 236 | `future-inevitability` | 0.408 |
| `future-superintelligence` | 1 | 67 | `AI-superintelligence` | 0.500 |
| `future-uncertainty` | 5 | 43, 44, 84, 236 | `future-inevitability` | 0.500 |
| `governance-responsible_development` | 4 | 73, 79 | `jobs-nurse` | 0.408 |
| `negative_impacts-dependence` | 13 | 24, 44, 64, 77, 80, 87, 100, 236 | `negative_impacts-control` | 0.667 |
| `negative_impacts-job_loss` | 2 | 48, 96 | `negative_impacts-job_destruction` | 0.750 |
| `negative_impacts-surveillance` | 7 | 11, 19, 40, 79, 81, 96 | `negative_impacts-control` | 0.667 |
| `positive_impacts-access` | 2 | 14, 15 | `impact-travel_immigration` | 0.667 |
| `positive_impacts-quality_of_life` | 5 | 19, 22, 33, 90 | `impact-travel_immigration` | 0.577 |

### Blind spots - human codes the machine never produced (106 codes, 291 segments)

The only place the negative example "you did not generate a new code" is observable:
a code never invented leaves no artefact inside a run. The segments themselves are in
the local run directory's `agreement.md`.

| human code | segments | responses | nearest machine code | cosine |
|---|---:|---|---|---:|
| `AI-autonomy` | 2 | 67, 100 | - | 0.000 |
| `AI-machine_communication` | 2 | 42, 67 | - | 0.000 |
| `AI-omnipotence` | 1 | 96 | - | 0.000 |
| `AI-self-modification` | 1 | 67 | - | 0.000 |
| `AI-speed` | 2 | 67, 96 | - | 0.000 |
| `AI-superintelligence` | 3 | 67 | `future-superintelligence` | 0.500 |
| `AI-surveillance` | 1 | 96 | `negative_impacts-surveillance` | 0.408 |
| `AI-tool` | 1 | 33 | - | 0.000 |
| `adoption-high` | 6 | 51, 53, 61, 82, 138, 236 | `adoption-everyday_life` | 0.408 |
| `adoption-necessity` | 3 | 42, 64 | `adoption-everyday_life` | 0.408 |
| `adoption-present` | 4 | 43, 64, 138 | `adoption-everyday_life` | 0.408 |
| `applications-chatbots` | 3 | 11, 53, 81 | `applications-automation` | 0.500 |
| `applications-decision-making` | 3 | 33, 82, 95 | `applications-automation` | 0.408 |
| `applications-deep_fakes` | 1 | 73 | `applications-automation` | 0.408 |
| `applications-financial_assistance` | 2 | 95 | `applications-automation` | 0.408 |
| `applications-friend` | 5 | 43, 82, 84 | `applications-automation` | 0.500 |
| `applications-information` | 2 | 22, 138 | `applications-automation` | 0.500 |
| `applications-medical_care` | 1 | 52 | `applications-automation` | 0.408 |
| `applications-meetings` | 3 | 22, 43, 45 | `applications-automation` | 0.500 |
| `applications-navigation` | 1 | 44 | `applications-automation` | 0.500 |
| `applications-personal_assistant` | 3 | 40, 81, 84 | `applications-automation` | 0.408 |
| `applications-planning` | 1 | 45 | `applications-automation` | 0.500 |
| `applications-problem-solving` | 2 | 84, 138 | `positive_impacts-problem_solving` | 0.577 |
| `applications-relationships` | 1 | 22 | `applications-automation` | 0.500 |
| `applications-research` | 1 | 95 | `applications-automation` | 0.500 |
| `applications-robotics` | 2 | 51, 52 | `applications-automation` | 0.500 |
| `applications-search` | 5 | 45, 80, 81, 90, 95 | `applications-automation` | 0.500 |
| `applications-self-driving_cars` | 4 | 15, 19, 51, 87 | `applications-automation` | 0.354 |
| `applications-simulation` | 1 | 90 | `applications-automation` | 0.500 |
| `applications-summarising` | 2 | 81, 90 | `applications-automation` | 0.500 |
| `applications-text_generation` | 1 | 45 | `applications-automation` | 0.408 |
| `applications-translation` | 1 | 44 | `applications-automation` | 0.500 |
| `applications-voice_recognition` | 1 | 81 | `applications-automation` | 0.408 |
| `ease-life` | 11 | 23, 40, 43, 51, 53, 61, 81, 84, 90 | `adoption-everyday_life` | 0.408 |
| `ease-travel` | 4 | 15, 19, 44, 53 | - | 0.000 |
| `ease-work` | 14 | 11, 14, 23, 24, 33, 43, 45, 46, 61, 81 | - | 0.000 |
| `efficiency` | 14 | 11, 15, 33, 45, 46, 48, 73, 77, 81, 85 | - | 0.000 |
| `future-hazard_avoidance` | 3 | 67, 73, 79 | `future-inevitability` | 0.408 |
| `future-negative` | 4 | 73, 79, 96, 100 | `future-inevitability` | 0.500 |
| `future-positive` | 10 | 45, 52, 53, 64, 84, 85, 88, 94 | `future-inevitability` | 0.500 |
| `future-transformation` | 8 | 51, 61, 64, 81, 82, 87, 90, 96 | `future-inevitability` | 0.500 |
| `impact-climate_change` | 1 | 77 | `adoption-social_change` | 0.333 |
| `impact-context-specific` | 2 | 77, 79 | `negative_impacts-dependence` | 0.333 |
| `impact-global` | 2 | 47, 90 | `negative_impacts-dependence` | 0.408 |
| `impact-jobs` | 5 | 47, 51, 73, 77 | `negative_impacts-job_loss` | 0.707 |
| `impact-misconception` | 1 | 82 | `negative_impacts-dependence` | 0.408 |
| `impact-travel_immigration` | 2 | 14, 15 | `positive_impacts-access` | 0.667 |
| `improvement-accuracy` | 6 | 11, 48, 51, 73, 84, 85 | - | 0.000 |
| `improvement-future_readiness` | 3 | 77, 85, 88 | `future-inevitability` | 0.408 |
| `improvement-personalisation` | 2 | 33, 90 | `applications-personalisation` | 0.500 |
| `improvement-quality_of_life` | 3 | 52, 85, 88 | `positive_impacts-quality_of_life` | 0.577 |
| `improvement-speed` | 3 | 42, 94, 95 | - | 0.000 |
| `improvement-teaching_learning` | 1 | 85 | - | 0.000 |
| `jobs-businessman` | 1 | 40 | `negative_impacts-job_loss` | 0.354 |
| `jobs-computer_operator` | 2 | 40, 51 | `negative_impacts-job_loss` | 0.289 |
| `jobs-driver` | 2 | 19, 40 | `negative_impacts-job_loss` | 0.354 |
| `jobs-nurse` | 1 | 52 | `governance-responsible_development` | 0.408 |
| `jobs-surveillance` | 1 | 40 | `negative_impacts-surveillance` | 0.408 |
| `jobs-tutor` | 2 | 40, 85 | `negative_impacts-job_loss` | 0.354 |
| `key_sectors-defence` | 1 | 33 | - | 0.000 |
| `key_sectors-disaster_management` | 1 | 33 | - | 0.000 |
| `key_sectors-education` | 3 | 33, 85, 96 | `applications-education` | 0.408 |
| `key_sectors-elder_care` | 2 | 52 | - | 0.000 |
| `key_sectors-entertainment` | 1 | 61 | - | 0.000 |
| `key_sectors-finance` | 1 | 95 | - | 0.000 |
| `key_sectors-health` | 3 | 47, 88, 94 | - | 0.000 |
| `key_sectors-marketing` | 1 | 14 | - | 0.000 |
| `key_sectors-technology` | 2 | 14, 96 | - | 0.000 |
| `key_sectors-transport` | 3 | 33, 87 | `applications-industry_and_transport` | 0.333 |
| `negative_impacts-control` | 1 | 79 | `negative_impacts-dependence` | 0.667 |
| `negative_impacts-danger_to_humans` | 2 | 67, 73 | `negative_impacts-dependence` | 0.577 |
| `negative_impacts-dependency` | 6 | 24, 44, 46, 64, 80, 100 | `negative_impacts-dependence` | 0.667 |
| `negative_impacts-deskilling` | 3 | 46, 80 | `negative_impacts-dependence` | 0.667 |
| `negative_impacts-domination` | 2 | 79, 80 | `negative_impacts-dependence` | 0.667 |
| `negative_impacts-enslavement` | 3 | 46, 67, 100 | `negative_impacts-dependence` | 0.667 |
| `negative_impacts-general` | 5 | 46, 61, 73, 79 | `negative_impacts-dependence` | 0.667 |
| `negative_impacts-immobility` | 2 | 80, 96 | `negative_impacts-dependence` | 0.667 |
| `negative_impacts-job_destruction` | 7 | 47, 48, 51, 64, 73, 77, 87 | `negative_impacts-job_loss` | 0.750 |
| `negative_impacts-lack_of_inclusion` | 1 | 77 | `negative_impacts-dependence` | 0.577 |
| `negative_impacts-lack_of_information` | 2 | 80, 100 | `negative_impacts-dependence` | 0.577 |
| `negative_impacts-laziness` | 3 | 24, 61 | `negative_impacts-dependence` | 0.667 |
| `negative_impacts-misuse` | 2 | 11, 79 | `negative_impacts-dependence` | 0.667 |
| `positive_impacts-automation` | 3 | 51, 53, 81 | `positive_impacts-access` | 0.667 |
| `positive_impacts-autonomy` | 1 | 48 | `positive_impacts-access` | 0.667 |
| `positive_impacts-corruption_reduction` | 1 | 48 | `positive_impacts-access` | 0.577 |
| `positive_impacts-cost_reduction` | 2 | 42, 88 | `positive_impacts-access` | 0.577 |
| `positive_impacts-drug_discovery` | 1 | 94 | `positive_impacts-access` | 0.577 |
| `positive_impacts-general` | 12 | 11, 46, 61, 64, 73, 79, 85, 88 | `positive_impacts-access` | 0.667 |
| `positive_impacts-greater_enjoyment` | 1 | 15 | `positive_impacts-access` | 0.577 |
| `positive_impacts-health` | 2 | 88, 94 | `positive_impacts-access` | 0.667 |
| `positive_impacts-invention` | 2 | 87, 94 | `positive_impacts-access` | 0.667 |
| `positive_impacts-personalisation` | 3 | 81, 94, 95 | `positive_impacts-access` | 0.667 |
| `positive_impacts-productivity` | 4 | 11, 77, 138 | `positive_impacts-access` | 0.667 |
| `positive_impacts-stress_reduction` | 2 | 24, 52 | `positive_impacts-access` | 0.577 |
| `positive_impacts-upskilling` | 1 | 138 | `positive_impacts-access` | 0.667 |
| `progress-economy` | 1 | 33 | - | 0.000 |
| `progress-holistic` | 3 | 24, 33, 43 | - | 0.000 |
| `progress-now` | 2 | 33, 40 | - | 0.000 |
| `requirements-basic_income` | 1 | 47 | - | 0.000 |
| `requirements-oversight` | 3 | 19, 48, 79 | - | 0.000 |
| `requirements-regulation` | 3 | 46, 73 | - | 0.000 |
| `safety-cybersecurity` | 2 | 14, 81 | - | 0.000 |
| `safety-home` | 1 | 52 | - | 0.000 |
| `safety-privacy` | 1 | 81 | - | 0.000 |
| `safety-travel` | 1 | 19 | - | 0.000 |
| `safety-women` | 1 | 14 | - | 0.000 |
