# 13 - Crosswalk: the machine's codebook mapped onto his

Space `lexical-v1-512`; tau_high 0.8, tau_low 0.45;
names only: no.
88 machine leaves against 117 of his.

> Compared as name + description on both sides (every leaf on both sides carries one); no fairness gap.

| band | machine leaves | what it means |
|---|---:|---|
| `same` | 0 | at or above tau_high 0.8 — the same concept |
| `grey` | 29 | between the thresholds — a live pipeline would ask the judge |
| `unmapped` | 59 | below tau_low 0.45 — nothing of his is close |

**Blind spots: 91 of his leaves nothing maps onto.**
**Inventions: 59 machine leaves with no counterpart of his.**

## Every machine leaf

`hungarian` is the one-to-one assignment over the whole vocabulary; `nearest` is the
unconstrained neighbour. They differ when a better-scoring leaf took the target first.

| machine leaf | hungarian target | score | band | nearest target | score | band |
|---|---|---:|---|---|---:|---|
| `AI-automation_of_repetitive_tasks` | - | - | - | `positive_impacts-jobs` | 0.344 | unmapped |
| `AI-complex_problem_solving` | `improvement-decision-making` | 0.518 | grey | `improvement-decision-making` | 0.518 | grey |
| `AI-creative_capability` | - | - | - | `AI-surveillance` | 0.445 | unmapped |
| `AI-daily_life_assistance` | `AI-tool` | 0.452 | grey | `AI-tool` | 0.452 | grey |
| `AI-disaster_management` | `key_sectors-disaster_management` | 0.593 | grey | `key_sectors-disaster_management` | 0.593 | grey |
| `AI-divine_connection` | - | - | - | `positive_impacts-autonomy` | 0.357 | unmapped |
| `AI-economic_efficiency` | - | - | - | `improvement-speed` | 0.369 | unmapped |
| `AI-economic_strengthening` | `progress-economy` | 0.710 | grey | `progress-economy` | 0.710 | grey |
| `AI-employment_transformation` | - | - | - | `positive_impacts-jobs` | 0.538 | grey |
| `AI-enhanced-communication` | - | - | - | `applications-relationships` | 0.420 | unmapped |
| `AI-entrepreneurial-support` | - | - | - | `AI-tool` | 0.399 | unmapped |
| `AI-facilitated-collaboration` | - | - | - | `negative_impacts-laziness` | 0.271 | unmapped |
| `AI-global_defence` | `key_sectors-defence` | 0.506 | grey | `key_sectors-defence` | 0.506 | grey |
| `AI-impact-immigration` | - | - | - | `positive_impacts-autonomy` | 0.468 | grey |
| `AI-impact-women_safety` | `safety-women` | 0.601 | grey | `safety-women` | 0.601 | grey |
| `AI-mindset_shift` | `adoption-necessity` | 0.465 | grey | `adoption-necessity` | 0.465 | grey |
| `AI-multi-use` | - | - | - | `AI-surveillance` | 0.415 | unmapped |
| `AI-need_for_awareness` | - | - | - | `requirements-regulation` | 0.374 | unmapped |
| `AI-omnipotence` | - | - | - | `AI-omnipotence` | 0.377 | unmapped |
| `AI-perception-central_role` | - | - | - | `future-positive` | 0.412 | unmapped |
| `AI-personalisation` | - | - | - | `improvement-personalisation` | 0.368 | unmapped |
| `AI-positive_outlook` | - | - | - | `positive_impacts-upskilling` | 0.447 | unmapped |
| `AI-productivity_enhancement` | - | - | - | `ease-work` | 0.403 | unmapped |
| `AI-role-expansion` | - | - | - | `AI-omnipotence` | 0.337 | unmapped |
| `AI-role-human_replacement` | - | - | - | `AI-autonomy` | 0.437 | unmapped |
| `AI-role_expansion` | - | - | - | `positive_impacts-upskilling` | 0.423 | unmapped |
| `AI-sector-focus-cyber_security` | - | - | - | `safety-cybersecurity` | 0.428 | unmapped |
| `AI-sector-focus-defence_education` | `key_sectors-education` | 0.475 | grey | `key_sectors-education` | 0.475 | grey |
| `AI-sector-focus-digital_marketing` | `key_sectors-marketing` | 0.599 | grey | `key_sectors-marketing` | 0.599 | grey |
| `AI-sector-focus-health` | `key_sectors-health` | 0.476 | grey | `key_sectors-health` | 0.476 | grey |
| `AI-sector_transformation` | - | - | - | `key_sectors-education` | 0.419 | unmapped |
| `AI-superintelligence` | `AI-superintelligence` | 0.471 | grey | `AI-superintelligence` | 0.471 | grey |
| `AI-threat-to-humanity` | `future-negative` | 0.453 | grey | `future-negative` | 0.453 | grey |
| `AI-ubiquity` | - | - | - | `AI-surveillance` | 0.321 | unmapped |
| `AI-utility` | `applications-personal_assistant` | 0.469 | grey | `applications-personal_assistant` | 0.469 | grey |
| `accessibility-assistance_for_disabled` | - | - | - | `applications-self-driving_cars` | 0.277 | unmapped |
| `accessibility-free_healthcare` | - | - | - | `progress-now` | 0.298 | unmapped |
| `ai-dependence-lifestyle` | - | - | - | `AI-omnipotence` | 0.376 | unmapped |
| `ai-productivity_enhancement` | - | - | - | `progress-economy` | 0.363 | unmapped |
| `ai-utility` | - | - | - | `AI-surveillance` | 0.371 | unmapped |
| `automation_of_repetitive_tasks` | - | - | - | `positive_impacts-automation` | 0.231 | unmapped |
| `benefit-reduced_stress` | - | - | - | `positive_impacts-stress_reduction` | 0.414 | unmapped |
| `complex_problem_solving-advance_analysis` | `positive_impacts-problem-solving` | 0.488 | grey | `positive_impacts-problem-solving` | 0.488 | grey |
| `concern-deepfakes` | - | - | - | `applications-deep_fakes` | 0.447 | unmapped |
| `concern-ethical_development` | - | - | - | `safety-women` | 0.255 | unmapped |
| `concern-human_dependency` | - | - | - | `negative_impacts-dependency` | 0.436 | unmapped |
| `concern-misuse` | - | - | - | `negative_impacts-enslavement` | 0.327 | unmapped |
| `concern-privacy_security` | - | - | - | `adoption-challenges-privacy` | 0.342 | unmapped |
| `daily_life_assistance-problem_resolution` | - | - | - | `safety-privacy` | 0.351 | unmapped |
| `economic_efficiency` | `impact-climate_change` | 0.598 | grey | `impact-climate_change` | 0.598 | grey |
| `economic_impact-productivity_gain` | - | - | - | `progress-economy` | 0.352 | unmapped |
| `economic_impact-universal_basic_income` | `requirements-basic_income` | 0.496 | grey | `requirements-basic_income` | 0.496 | grey |
| `education-literacy_requirement` | - | - | - | `AI-surveillance` | 0.328 | unmapped |
| `education-sector-transformation` | - | - | - | `key_sectors-education` | 0.360 | unmapped |
| `employment_transformation` | `positive_impacts-jobs` | 0.477 | grey | `positive_impacts-jobs` | 0.477 | grey |
| `impact-communication_enhancement` | - | - | - | `negative_impacts-lack_of_information` | 0.312 | unmapped |
| `impact-digital_connectivity` | - | - | - | `applications-relationships` | 0.298 | unmapped |
| `impact-digital_exclusion` | - | - | - | `negative_impacts-danger_to_humans` | 0.456 | grey |
| `impact-public_safety` | - | - | - | `key_sectors-disaster_management` | 0.439 | unmapped |
| `impact-technological_advancement` | - | - | - | `progress-holistic` | 0.402 | unmapped |
| `impact-work_ease` | - | - | - | `ease-work` | 0.385 | unmapped |
| `labor-competitive_advantage` | - | - | - | `adoption-present` | 0.324 | unmapped |
| `labor-job_transformation` | - | - | - | `impact-jobs` | 0.400 | unmapped |
| `negative_impacts-cybersecurity_risks` | - | - | - | `positive_impacts-drug_discovery` | 0.232 | unmapped |
| `negative_impacts-human_subjugation` | `negative_impacts-danger_to_humans` | 0.517 | grey | `negative_impacts-danger_to_humans` | 0.517 | grey |
| `negative_impacts-job_destruction` | `negative_impacts-job_destruction` | 0.547 | grey | `negative_impacts-job_destruction` | 0.547 | grey |
| `negative_impacts-laziness` | `negative_impacts-laziness` | 0.545 | grey | `negative_impacts-laziness` | 0.545 | grey |
| `negative_impacts-misuse` | `negative_impacts-misuse` | 0.579 | grey | `negative_impacts-misuse` | 0.579 | grey |
| `perception-technological_luck` | - | - | - | `ease-life` | 0.302 | unmapped |
| `personalisation-virtual_trials` | - | - | - | `applications-simulation` | 0.441 | unmapped |
| `positive_outcomes-work_relief` | - | - | - | `ease-work` | 0.458 | grey |
| `positive_outlook` | `future-positive` | 0.576 | grey | `future-positive` | 0.576 | grey |
| `resource-efficiency` | - | - | - | `applications-information` | 0.322 | unmapped |
| `safety-improvements-shelter_security` | - | - | - | `safety-home` | 0.399 | unmapped |
| `safety-reduced_accidents` | - | - | - | `negative_impacts-enslavement` | 0.316 | unmapped |
| `safety_improvements` | - | - | - | `safety-women` | 0.217 | unmapped |
| `sector-focus-cyber_security` | `safety-cybersecurity` | 0.502 | grey | `safety-cybersecurity` | 0.502 | grey |
| `sector-focus-digital_marketing` | - | - | - | `key_sectors-marketing` | 0.523 | grey |
| `sector-focus-transportation` | - | - | - | `future-transformation` | 0.312 | unmapped |
| `sector_transformation` | - | - | - | `future-transformation` | 0.435 | unmapped |
| `security-cyber_security` | - | - | - | `safety-cybersecurity` | 0.327 | unmapped |
| `society-digital-transformation` | - | - | - | `positive_impacts-invention` | 0.205 | unmapped |
| `transport_automation` | - | - | - | `key_sectors-transport` | 0.279 | unmapped |
| `transportation-autonomous_vehicles` | `applications-self-driving_cars` | 0.464 | grey | `applications-self-driving_cars` | 0.464 | grey |
| `transportation-navigation_assistance` | - | - | - | `applications-navigation` | 0.378 | unmapped |
| `ubiquity` | - | - | - | `positive_impacts-invention` | 0.303 | unmapped |
| `user_experience_relaxation` | - | - | - | `positive_impacts-greater_enjoyment` | 0.365 | unmapped |
| `utility-work_efficiency` | - | - | - | `efficiency` | 0.404 | unmapped |

## His families, and where the machine's leaves land

| his family | his leaves | machine leaves landing here | from machine families | blind spots |
|---|---:|---:|---|---:|
| `AI` | 8 | 2 | `AI` 2 | 6 |
| `adoption` | 6 | 1 | `AI` 1 | 5 |
| `applications` | 22 | 2 | `AI` 1, `transportation` 1 | 20 |
| `ease` | 3 | 1 | `positive_outcomes` 1 | 2 |
| `efficiency` | 1 | 0 | - | 1 |
| `future` | 5 | 2 | `AI` 1, `positive_outlook` 1 | 3 |
| `impact` | 6 | 1 | `economic_efficiency` 1 | 5 |
| `improvement` | 8 | 1 | `AI` 1 | 7 |
| `jobs` | 6 | 0 | - | 6 |
| `key_sectors` | 11 | 6 | `AI` 5, `sector` 1 | 6 |
| `negative_impacts` | 13 | 5 | `impact` 1, `negative_impacts` 4 | 9 |
| `positive_impacts` | 16 | 4 | `AI` 2, `complex_problem_solving` 1, `employment_transformation` 1 | 13 |
| `progress` | 3 | 1 | `AI` 1 | 2 |
| `requirements` | 4 | 1 | `economic_impact` 1 | 3 |
| `safety` | 5 | 2 | `AI` 1, `sector` 1 | 3 |

## The machine's families, and where they land in his tree

| machine family | leaves | lands in | scattered | unmapped |
|---|---:|---|---|---:|
| `AI` | 35 | `AI` 2, `adoption` 1, `applications` 1, `future` 1, `improvement` 1, `key_sectors` 5, `positive_impacts` 2, `progress` 1, `safety` 1 | yes | 20 |
| `accessibility` | 2 | - | no | 2 |
| `ai` | 3 | - | no | 3 |
| `automation_of_repetitive_tasks` | 1 | - | no | 1 |
| `benefit` | 1 | - | no | 1 |
| `complex_problem_solving` | 1 | `positive_impacts` 1 | no | 0 |
| `concern` | 5 | - | no | 5 |
| `daily_life_assistance` | 1 | - | no | 1 |
| `economic_efficiency` | 1 | `impact` 1 | no | 0 |
| `economic_impact` | 2 | `requirements` 1 | no | 1 |
| `education` | 2 | - | no | 2 |
| `employment_transformation` | 1 | `positive_impacts` 1 | no | 0 |
| `impact` | 6 | `negative_impacts` 1 | no | 5 |
| `labor` | 2 | - | no | 2 |
| `negative_impacts` | 5 | `negative_impacts` 4 | no | 1 |
| `perception` | 1 | - | no | 1 |
| `personalisation` | 1 | - | no | 1 |
| `positive_outcomes` | 1 | `ease` 1 | no | 0 |
| `positive_outlook` | 1 | `future` 1 | no | 0 |
| `resource` | 1 | - | no | 1 |
| `safety` | 2 | - | no | 2 |
| `safety_improvements` | 1 | - | no | 1 |
| `sector` | 3 | `key_sectors` 1, `safety` 1 | yes | 1 |
| `sector_transformation` | 1 | - | no | 1 |
| `security` | 1 | - | no | 1 |
| `society` | 1 | - | no | 1 |
| `transport_automation` | 1 | - | no | 1 |
| `transportation` | 2 | `applications` 1 | no | 1 |
| `ubiquity` | 1 | - | no | 1 |
| `user_experience_relaxation` | 1 | - | no | 1 |
| `utility` | 1 | - | no | 1 |

### Blind spots — his leaves nothing maps onto

`AI-autonomy`, `AI-machine_communication`, `AI-omnipotence`, `AI-self-modification`, `AI-speed`, `AI-surveillance`, `adoption-challenges-job_losses`, `adoption-challenges-privacy`, `adoption-challenges-safety`, `adoption-high`, `adoption-present`, `applications-chatbots`, `applications-decision-making`, `applications-deep_fakes`, `applications-financial_assistance`, `applications-friend`, `applications-information`, `applications-medical_care`, `applications-meetings`, `applications-navigation`, `applications-planning`, `applications-problem-solving`, `applications-relationships`, `applications-research`, `applications-robotics`, `applications-search`, `applications-simulation`, `applications-summarising`, `applications-text_generation`, `applications-translation`, `applications-voice_recognition`, `ease-life`, `ease-travel`, `efficiency`, `future-hazard_avoidance`, `future-inevitability`, `future-transformation`, `impact-context-specific`, `impact-global`, `impact-jobs`, `impact-misconception`, `impact-travel_immigration`, `improvement-accuracy`, `improvement-future_readiness`, `improvement-health`, `improvement-personalisation`, `improvement-quality_of_life`, `improvement-speed`, `improvement-teaching_learning`, `jobs-businessman`, `jobs-computer_operator`, `jobs-driver`, `jobs-nurse`, `jobs-surveillance`, `jobs-tutor`, `key_sectors-elder_care`, `key_sectors-entertainment`, `key_sectors-finance`, `key_sectors-manufacturing`, `key_sectors-technology`, `key_sectors-transport`, `negative_impacts-control`, `negative_impacts-dependency`, `negative_impacts-deskilling`, `negative_impacts-domination`, `negative_impacts-enslavement`, `negative_impacts-general`, `negative_impacts-immobility`, `negative_impacts-lack_of_inclusion`, `negative_impacts-lack_of_information`, `positive_impacts-accessibility`, `positive_impacts-automation`, `positive_impacts-corruption_reduction`, `positive_impacts-cost_reduction`, `positive_impacts-drug_discovery`, `positive_impacts-general`, `positive_impacts-greater_enjoyment`, `positive_impacts-health`, `positive_impacts-invention`, `positive_impacts-personalisation`, `positive_impacts-productivity`, `positive_impacts-stress_reduction`, `positive_impacts-upskilling`, `progress-holistic`, `progress-now`, `requirements-informed_engagement`, `requirements-oversight`, `requirements-regulation`, `safety-home`, `safety-privacy`, `safety-travel`

### Inventions — machine leaves with no counterpart of his

`AI-automation_of_repetitive_tasks`, `AI-creative_capability`, `AI-divine_connection`, `AI-economic_efficiency`, `AI-enhanced-communication`, `AI-entrepreneurial-support`, `AI-facilitated-collaboration`, `AI-multi-use`, `AI-need_for_awareness`, `AI-omnipotence`, `AI-perception-central_role`, `AI-personalisation`, `AI-positive_outlook`, `AI-productivity_enhancement`, `AI-role-expansion`, `AI-role-human_replacement`, `AI-role_expansion`, `AI-sector-focus-cyber_security`, `AI-sector_transformation`, `AI-ubiquity`, `accessibility-assistance_for_disabled`, `accessibility-free_healthcare`, `ai-dependence-lifestyle`, `ai-productivity_enhancement`, `ai-utility`, `automation_of_repetitive_tasks`, `benefit-reduced_stress`, `concern-deepfakes`, `concern-ethical_development`, `concern-human_dependency`, `concern-misuse`, `concern-privacy_security`, `daily_life_assistance-problem_resolution`, `economic_impact-productivity_gain`, `education-literacy_requirement`, `education-sector-transformation`, `impact-communication_enhancement`, `impact-digital_connectivity`, `impact-public_safety`, `impact-technological_advancement`, `impact-work_ease`, `labor-competitive_advantage`, `labor-job_transformation`, `negative_impacts-cybersecurity_risks`, `perception-technological_luck`, `personalisation-virtual_trials`, `resource-efficiency`, `safety-improvements-shelter_security`, `safety-reduced_accidents`, `safety_improvements`, `sector-focus-transportation`, `sector_transformation`, `security-cyber_security`, `society-digital-transformation`, `transport_automation`, `transportation-navigation_assistance`, `ubiquity`, `user_experience_relaxation`, `utility-work_efficiency`
