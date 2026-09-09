# 06 - Concurrent validation: his coding against the machine's

The machine side here is the offline stand-in coder (a deterministic keyword table used
so the pipeline runs without a model or a key). Its agreement with an expert is not the
question; whether the harness measures and explains a disagreement on real inputs is.

## As first run: machine codes carry descriptions, his do not

Embedding space `lexical-v1-512`, tau_high 0.8: 1 of 76 human codes matched to one of 18 machine codes.

| scope | precision | recall | F1 | kappa | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| all codes (union vocabulary) | 0.000 | 0.000 | 0.000 | -0.059 | 0 | 85 | 134 |
| matched codes only | 0.000 | 0.000 | 0.000 | -0.087 | 0 | 1 | 4 |

| segment level | precision | recall | F1 |
|---|---:|---:|---:|
| span-overlap weighted | 0.000 | 0.000 | 0.000 |
| strict (overlap >= 0.5) | 0.000 | 0.000 | 0.000 |

Right code, wrong place: 0; mean overlap on shared codes 0.000.

### Code matching (Hungarian assignment, nearest pairs)

| human code | machine code | similarity | accepted |
|---|---|---:|---|
| `future-inevitability` | `future-inevitability` | 1.000 | yes |
| `positive_impacts-problem-solving` | `positive_impacts-problem_solving` | 0.696 | no |
| `applications-medical_care` | `applications-healthcare` | 0.577 | no |
| `negative_impacts-misuse` | `negative_impacts-surveillance` | 0.522 | no |
| `positive_impacts-jobs` | `positive_impacts-job_creation` | 0.480 | no |
| `improvement-quality_of_life` | `positive_impacts-quality_of_life` | 0.472 | no |
| `applications-robotics` | `applications-automation` | 0.447 | no |
| `improvement-personalisation` | `applications-personalisation` | 0.426 | no |
| `negative_impacts-job_destruction` | `negative_impacts-job_loss` | 0.416 | no |
| `negative_impacts-dependency` | `negative_impacts-dependence` | 0.385 | no |
| `ease-life` | `adoption-everyday_life` | 0.363 | no |
| `impact-travel_immigration` | `positive_impacts-access` | 0.348 | no |
| `applications-decision-making` | `applications-data_driven_systems` | 0.324 | no |
| `key_sectors-transport` | `applications-industry_and_transport` | 0.285 | no |
| `future-transformation` | `future-uncertainty` | 0.250 | no |
| `applications-chatbots` | `applications-education` | 0.250 | no |
| `AI-tool` | `adoption-social_change` | 0.224 | no |
| `future-positive` | `future-imagined_scenario` | 0.215 | no |

### Over-coding - machine codes with no human counterpart (17 codes, 196 segments)

| machine code | segments | responses | nearest human code | cosine |
|---|---:|---|---|---:|
| `adoption-everyday_life` | 2 | 42, 61 | `ease-life` | 0.363 |
| `adoption-social_change` | 66 | 11, 14, 15, 19, 22, 23, 24, 33, 40, 42, 44, 45, 46, 47, 48, 51, 52, 53, 61, 1044 | `AI-tool` | 0.224 |
| `applications-automation` | 8 | 42, 51, 53 | `applications-robotics` | 0.447 |
| `applications-data_driven_systems` | 4 | 19, 48 | `improvement-personalisation` | 0.336 |
| `applications-education` | 5 | 33, 40, 45, 53, 61 | `AI-tool` | 0.250 |
| `applications-healthcare` | 3 | 47, 52 | `applications-medical_care` | 0.577 |
| `applications-industry_and_transport` | 8 | 14, 15, 19, 47, 51 | `key_sectors-transport` | 0.285 |
| `applications-personalisation` | 1 | 33 | `improvement-personalisation` | 0.426 |
| `future-imagined_scenario` | 68 | 11, 14, 15, 19, 22, 23, 24, 33, 40, 42, 44, 45, 46, 47, 48, 51, 52, 53, 61, 1044 | `future-positive` | 0.215 |
| `future-uncertainty` | 3 | 44, 1044 | `future-inevitability` | 0.320 |
| `negative_impacts-dependence` | 4 | 24, 1044 | `negative_impacts-dependency` | 0.385 |
| `negative_impacts-job_loss` | 1 | 48 | `negative_impacts-job_destruction` | 0.416 |
| `negative_impacts-surveillance` | 3 | 11, 19, 40 | `negative_impacts-misuse` | 0.522 |
| `positive_impacts-access` | 2 | 14, 15 | `impact-travel_immigration` | 0.348 |
| `positive_impacts-job_creation` | 3 | 22, 42, 51 | `positive_impacts-jobs` | 0.480 |
| `positive_impacts-problem_solving` | 12 | 11, 22, 33, 42, 45, 48, 51, 53 | `positive_impacts-problem-solving` | 0.696 |
| `positive_impacts-quality_of_life` | 3 | 19, 22, 33 | `improvement-quality_of_life` | 0.472 |

### Blind spots - human codes the machine never produced (75 codes, 143 segments)

The only place the negative example "you did not generate a new code" is observable:
a code never invented leaves no artefact inside a run. The segments themselves are in
the local run directory's `agreement.md`.

| human code | segments | responses | nearest machine code | cosine |
|---|---:|---|---|---:|
| `AI-machine_communication` | 1 | 42 | `future-uncertainty` | 0.204 |
| `AI-tool` | 1 | 33 | `future-uncertainty` | 0.250 |
| `adoption-high` | 3 | 51, 53, 61 | `adoption-social_change` | 0.224 |
| `adoption-necessity` | 1 | 42 | `adoption-social_change` | 0.224 |
| `adoption-present` | 1 | 44 | `adoption-social_change` | 0.224 |
| `applications-chatbots` | 2 | 11, 53 | `future-uncertainty` | 0.250 |
| `applications-decision-making` | 1 | 33 | `applications-data_driven_systems` | 0.324 |
| `applications-friend` | 1 | 44 | `applications-education` | 0.250 |
| `applications-information` | 1 | 22 | `applications-education` | 0.250 |
| `applications-medical_care` | 1 | 52 | `applications-healthcare` | 0.577 |
| `applications-meetings` | 3 | 22, 44, 45 | `applications-education` | 0.250 |
| `applications-navigation` | 1 | 1044 | `applications-education` | 0.250 |
| `applications-personal_assistant` | 1 | 40 | `applications-education` | 0.204 |
| `applications-planning` | 1 | 45 | `applications-education` | 0.250 |
| `applications-relationships` | 1 | 22 | `applications-education` | 0.250 |
| `applications-robotics` | 3 | 51, 52 | `applications-automation` | 0.447 |
| `applications-search` | 1 | 45 | `applications-education` | 0.250 |
| `applications-self-driving_cars` | 3 | 15, 19, 51 | `applications-education` | 0.177 |
| `applications-text_generation` | 1 | 45 | `applications-education` | 0.204 |
| `applications-translation` | 1 | 1044 | `applications-education` | 0.250 |
| `ease-life` | 6 | 23, 40, 44, 51, 53, 61 | `adoption-everyday_life` | 0.363 |
| `ease-travel` | 4 | 15, 19, 53, 1044 | `applications-data_driven_systems` | 0.198 |
| `ease-work` | 11 | 11, 14, 23, 24, 33, 44, 45, 46, 61 | `negative_impacts-job_loss` | 0.392 |
| `efficiency` | 10 | 11, 15, 33, 42, 45, 46, 48 | - | 0.000 |
| `future-positive` | 4 | 45, 52, 53 | `future-uncertainty` | 0.250 |
| `future-transformation` | 2 | 51, 61 | `future-uncertainty` | 0.250 |
| `impact-global` | 1 | 47 | `positive_impacts-problem_solving` | 0.346 |
| `impact-jobs` | 2 | 47, 51 | `negative_impacts-job_loss` | 0.392 |
| `impact-travel_immigration` | 2 | 14, 15 | `positive_impacts-problem_solving` | 0.423 |
| `improvement-accuracy` | 3 | 11, 48, 51 | - | 0.000 |
| `improvement-personalisation` | 1 | 33 | `applications-personalisation` | 0.426 |
| `improvement-quality_of_life` | 1 | 52 | `positive_impacts-quality_of_life` | 0.472 |
| `improvement-speed` | 1 | 42 | - | 0.000 |
| `jobs-businessman` | 1 | 40 | `applications-industry_and_transport` | 0.206 |
| `jobs-computer_operator` | 2 | 40, 51 | `adoption-everyday_life` | 0.175 |
| `jobs-driver` | 2 | 19, 40 | `applications-industry_and_transport` | 0.206 |
| `jobs-nurse` | 1 | 52 | `negative_impacts-surveillance` | 0.213 |
| `jobs-surveillance` | 1 | 40 | `negative_impacts-surveillance` | 0.213 |
| `jobs-tutor` | 1 | 40 | `applications-industry_and_transport` | 0.206 |
| `key-sectors-elder_care` | 2 | 52 | `applications-healthcare` | 0.167 |
| `key_sectors-defence` | 1 | 33 | `applications-healthcare` | 0.192 |
| `key_sectors-disaster_management` | 1 | 33 | `positive_impacts-quality_of_life` | 0.152 |
| `key_sectors-education` | 1 | 33 | `applications-education` | 0.204 |
| `key_sectors-entertainment` | 1 | 61 | `positive_impacts-quality_of_life` | 0.175 |
| `key_sectors-health` | 1 | 47 | `positive_impacts-quality_of_life` | 0.175 |
| `key_sectors-marketing` | 1 | 14 | `positive_impacts-quality_of_life` | 0.175 |
| `key_sectors-technology` | 1 | 14 | `positive_impacts-quality_of_life` | 0.175 |
| `key_sectors-transport` | 1 | 33 | `applications-industry_and_transport` | 0.285 |
| `negative_impacts-dependency` | 3 | 24, 46, 1044 | `negative_impacts-dependence` | 0.385 |
| `negative_impacts-deskilling` | 1 | 46 | `negative_impacts-dependence` | 0.385 |
| `negative_impacts-enslavement` | 1 | 46 | `negative_impacts-dependence` | 0.385 |
| `negative_impacts-general` | 2 | 46, 61 | `negative_impacts-dependence` | 0.385 |
| `negative_impacts-job_destruction` | 3 | 47, 48, 51 | `negative_impacts-job_loss` | 0.416 |
| `negative_impacts-laziness` | 3 | 24, 61 | `negative_impacts-dependence` | 0.385 |
| `negative_impacts-misuse` | 2 | 11, 33 | `negative_impacts-surveillance` | 0.522 |
| `positive_impacts-automation` | 2 | 51, 53 | `positive_impacts-problem_solving` | 0.423 |
| `positive_impacts-autonomy` | 1 | 48 | `positive_impacts-problem_solving` | 0.423 |
| `positive_impacts-corruption_reduction` | 1 | 48 | `positive_impacts-problem_solving` | 0.367 |
| `positive_impacts-cost_reduction` | 1 | 42 | `positive_impacts-problem_solving` | 0.367 |
| `positive_impacts-general` | 5 | 11, 46, 61 | `positive_impacts-problem_solving` | 0.423 |
| `positive_impacts-greater_enjoyment` | 1 | 15 | `positive_impacts-problem_solving` | 0.367 |
| `positive_impacts-jobs` | 1 | 42 | `positive_impacts-job_creation` | 0.480 |
| `positive_impacts-problem-solving` | 4 | 11, 33 | `positive_impacts-problem_solving` | 0.696 |
| `positive_impacts-productivity` | 1 | 11 | `positive_impacts-problem_solving` | 0.423 |
| `positive_impacts-stress_reduction` | 2 | 24, 52 | `positive_impacts-problem_solving` | 0.367 |
| `progress-economy` | 1 | 33 | `adoption-everyday_life` | 0.215 |
| `progress-holistic` | 3 | 24, 33, 44 | `adoption-everyday_life` | 0.215 |
| `progress-now` | 2 | 33, 40 | `adoption-everyday_life` | 0.215 |
| `requirements-basic_income` | 1 | 47 | `positive_impacts-quality_of_life` | 0.175 |
| `requirements-oversight` | 2 | 19, 48 | `positive_impacts-job_creation` | 0.196 |
| `requirements-regulation` | 1 | 46 | `positive_impacts-job_creation` | 0.196 |
| `safety-cybersecurity` | 1 | 14 | - | 0.000 |
| `safety-home` | 1 | 52 | - | 0.000 |
| `safety-travel` | 1 | 19 | - | 0.000 |
| `safety-women` | 1 | 14 | `applications-data_driven_systems` | 0.198 |

## Name against name: no descriptions on either side

Embedding space `lexical-v1-512`, tau_high 0.8: 3 of 76 human codes matched to one of 18 machine codes.

| scope | precision | recall | F1 | kappa | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| all codes (union vocabulary) | 0.035 | 0.022 | 0.027 | -0.032 | 3 | 82 | 131 |
| matched codes only | 0.250 | 0.429 | 0.316 | 0.198 | 3 | 9 | 4 |

| segment level | precision | recall | F1 |
|---|---:|---:|---:|
| span-overlap weighted | 0.009 | 0.011 | 0.010 |
| strict (overlap >= 0.5) | 0.010 | 0.014 | 0.012 |

Right code, wrong place: 4; mean overlap on shared codes 0.286.

### Code matching (Hungarian assignment, nearest pairs)

| human code | machine code | similarity | accepted |
|---|---|---:|---|
| `future-inevitability` | `future-inevitability` | 1.000 | yes |
| `positive_impacts-problem-solving` | `positive_impacts-problem_solving` | 1.000 | yes |
| `positive_impacts-jobs` | `positive_impacts-job_creation` | 0.866 | yes |
| `negative_impacts-job_destruction` | `negative_impacts-job_loss` | 0.750 | no |
| `impact-travel_immigration` | `positive_impacts-access` | 0.667 | no |
| `negative_impacts-dependency` | `negative_impacts-dependence` | 0.667 | no |
| `negative_impacts-deskilling` | `negative_impacts-surveillance` | 0.667 | no |
| `improvement-quality_of_life` | `positive_impacts-quality_of_life` | 0.577 | no |
| `applications-chatbots` | `applications-automation` | 0.500 | no |
| `applications-information` | `applications-education` | 0.500 | no |
| `applications-meetings` | `applications-healthcare` | 0.500 | no |
| `applications-planning` | `applications-personalisation` | 0.500 | no |
| `future-transformation` | `future-uncertainty` | 0.500 | no |
| `adoption-high` | `adoption-everyday_life` | 0.408 | no |
| `adoption-necessity` | `adoption-social_change` | 0.408 | no |
| `applications-navigation` | `applications-industry_and_transport` | 0.408 | no |
| `future-positive` | `future-imagined_scenario` | 0.408 | no |
| `applications-friend` | `applications-data_driven_systems` | 0.354 | no |

### Over-coding - machine codes with no human counterpart (15 codes, 181 segments)

| machine code | segments | responses | nearest human code | cosine |
|---|---:|---|---|---:|
| `adoption-everyday_life` | 2 | 42, 61 | `adoption-high` | 0.408 |
| `adoption-social_change` | 66 | 11, 14, 15, 19, 22, 23, 24, 33, 40, 42, 44, 45, 46, 47, 48, 51, 52, 53, 61, 1044 | `adoption-high` | 0.408 |
| `applications-automation` | 8 | 42, 51, 53 | `applications-chatbots` | 0.500 |
| `applications-data_driven_systems` | 4 | 19, 48 | `applications-chatbots` | 0.354 |
| `applications-education` | 5 | 33, 40, 45, 53, 61 | `applications-chatbots` | 0.500 |
| `applications-healthcare` | 3 | 47, 52 | `applications-chatbots` | 0.500 |
| `applications-industry_and_transport` | 8 | 14, 15, 19, 47, 51 | `applications-chatbots` | 0.408 |
| `applications-personalisation` | 1 | 33 | `applications-chatbots` | 0.500 |
| `future-imagined_scenario` | 68 | 11, 14, 15, 19, 22, 23, 24, 33, 40, 42, 44, 45, 46, 47, 48, 51, 52, 53, 61, 1044 | `future-inevitability` | 0.408 |
| `future-uncertainty` | 3 | 44, 1044 | `future-inevitability` | 0.500 |
| `negative_impacts-dependence` | 4 | 24, 1044 | `negative_impacts-dependency` | 0.667 |
| `negative_impacts-job_loss` | 1 | 48 | `negative_impacts-job_destruction` | 0.750 |
| `negative_impacts-surveillance` | 3 | 11, 19, 40 | `negative_impacts-dependency` | 0.667 |
| `positive_impacts-access` | 2 | 14, 15 | `impact-travel_immigration` | 0.667 |
| `positive_impacts-quality_of_life` | 3 | 19, 22, 33 | `impact-travel_immigration` | 0.577 |

### Blind spots - human codes the machine never produced (73 codes, 138 segments)

The only place the negative example "you did not generate a new code" is observable:
a code never invented leaves no artefact inside a run. The segments themselves are in
the local run directory's `agreement.md`.

| human code | segments | responses | nearest machine code | cosine |
|---|---:|---|---|---:|
| `AI-machine_communication` | 1 | 42 | - | 0.000 |
| `AI-tool` | 1 | 33 | - | 0.000 |
| `adoption-high` | 3 | 51, 53, 61 | `adoption-everyday_life` | 0.408 |
| `adoption-necessity` | 1 | 42 | `adoption-everyday_life` | 0.408 |
| `adoption-present` | 1 | 44 | `adoption-everyday_life` | 0.408 |
| `applications-chatbots` | 2 | 11, 53 | `applications-automation` | 0.500 |
| `applications-decision-making` | 1 | 33 | `applications-automation` | 0.408 |
| `applications-friend` | 1 | 44 | `applications-automation` | 0.500 |
| `applications-information` | 1 | 22 | `applications-automation` | 0.500 |
| `applications-medical_care` | 1 | 52 | `applications-automation` | 0.408 |
| `applications-meetings` | 3 | 22, 44, 45 | `applications-automation` | 0.500 |
| `applications-navigation` | 1 | 1044 | `applications-automation` | 0.500 |
| `applications-personal_assistant` | 1 | 40 | `applications-automation` | 0.408 |
| `applications-planning` | 1 | 45 | `applications-automation` | 0.500 |
| `applications-relationships` | 1 | 22 | `applications-automation` | 0.500 |
| `applications-robotics` | 3 | 51, 52 | `applications-automation` | 0.500 |
| `applications-search` | 1 | 45 | `applications-automation` | 0.500 |
| `applications-self-driving_cars` | 3 | 15, 19, 51 | `applications-automation` | 0.354 |
| `applications-text_generation` | 1 | 45 | `applications-automation` | 0.408 |
| `applications-translation` | 1 | 1044 | `applications-automation` | 0.500 |
| `ease-life` | 6 | 23, 40, 44, 51, 53, 61 | `adoption-everyday_life` | 0.408 |
| `ease-travel` | 4 | 15, 19, 53, 1044 | - | 0.000 |
| `ease-work` | 11 | 11, 14, 23, 24, 33, 44, 45, 46, 61 | - | 0.000 |
| `efficiency` | 10 | 11, 15, 33, 42, 45, 46, 48 | - | 0.000 |
| `future-positive` | 4 | 45, 52, 53 | `future-inevitability` | 0.500 |
| `future-transformation` | 2 | 51, 61 | `future-inevitability` | 0.500 |
| `impact-global` | 1 | 47 | `negative_impacts-dependence` | 0.408 |
| `impact-jobs` | 2 | 47, 51 | `negative_impacts-job_loss` | 0.707 |
| `impact-travel_immigration` | 2 | 14, 15 | `positive_impacts-access` | 0.667 |
| `improvement-accuracy` | 3 | 11, 48, 51 | - | 0.000 |
| `improvement-personalisation` | 1 | 33 | `applications-personalisation` | 0.500 |
| `improvement-quality_of_life` | 1 | 52 | `positive_impacts-quality_of_life` | 0.577 |
| `improvement-speed` | 1 | 42 | - | 0.000 |
| `jobs-businessman` | 1 | 40 | `negative_impacts-job_loss` | 0.354 |
| `jobs-computer_operator` | 2 | 40, 51 | `negative_impacts-job_loss` | 0.289 |
| `jobs-driver` | 2 | 19, 40 | `negative_impacts-job_loss` | 0.354 |
| `jobs-nurse` | 1 | 52 | `negative_impacts-job_loss` | 0.354 |
| `jobs-surveillance` | 1 | 40 | `negative_impacts-surveillance` | 0.408 |
| `jobs-tutor` | 1 | 40 | `negative_impacts-job_loss` | 0.354 |
| `key-sectors-elder_care` | 2 | 52 | - | 0.000 |
| `key_sectors-defence` | 1 | 33 | - | 0.000 |
| `key_sectors-disaster_management` | 1 | 33 | - | 0.000 |
| `key_sectors-education` | 1 | 33 | `applications-education` | 0.408 |
| `key_sectors-entertainment` | 1 | 61 | - | 0.000 |
| `key_sectors-health` | 1 | 47 | - | 0.000 |
| `key_sectors-marketing` | 1 | 14 | - | 0.000 |
| `key_sectors-technology` | 1 | 14 | - | 0.000 |
| `key_sectors-transport` | 1 | 33 | `applications-industry_and_transport` | 0.333 |
| `negative_impacts-dependency` | 3 | 24, 46, 1044 | `negative_impacts-dependence` | 0.667 |
| `negative_impacts-deskilling` | 1 | 46 | `negative_impacts-dependence` | 0.667 |
| `negative_impacts-enslavement` | 1 | 46 | `negative_impacts-dependence` | 0.667 |
| `negative_impacts-general` | 2 | 46, 61 | `negative_impacts-dependence` | 0.667 |
| `negative_impacts-job_destruction` | 3 | 47, 48, 51 | `negative_impacts-job_loss` | 0.750 |
| `negative_impacts-laziness` | 3 | 24, 61 | `negative_impacts-dependence` | 0.667 |
| `negative_impacts-misuse` | 2 | 11, 33 | `negative_impacts-dependence` | 0.667 |
| `positive_impacts-automation` | 2 | 51, 53 | `positive_impacts-access` | 0.667 |
| `positive_impacts-autonomy` | 1 | 48 | `positive_impacts-access` | 0.667 |
| `positive_impacts-corruption_reduction` | 1 | 48 | `positive_impacts-access` | 0.577 |
| `positive_impacts-cost_reduction` | 1 | 42 | `positive_impacts-access` | 0.577 |
| `positive_impacts-general` | 5 | 11, 46, 61 | `positive_impacts-access` | 0.667 |
| `positive_impacts-greater_enjoyment` | 1 | 15 | `positive_impacts-access` | 0.577 |
| `positive_impacts-productivity` | 1 | 11 | `positive_impacts-access` | 0.667 |
| `positive_impacts-stress_reduction` | 2 | 24, 52 | `positive_impacts-access` | 0.577 |
| `progress-economy` | 1 | 33 | - | 0.000 |
| `progress-holistic` | 3 | 24, 33, 44 | - | 0.000 |
| `progress-now` | 2 | 33, 40 | - | 0.000 |
| `requirements-basic_income` | 1 | 47 | - | 0.000 |
| `requirements-oversight` | 2 | 19, 48 | - | 0.000 |
| `requirements-regulation` | 1 | 46 | - | 0.000 |
| `safety-cybersecurity` | 1 | 14 | - | 0.000 |
| `safety-home` | 1 | 52 | - | 0.000 |
| `safety-travel` | 1 | 19 | - | 0.000 |
| `safety-women` | 1 | 14 | - | 0.000 |
