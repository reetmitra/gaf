# 13 - Crosswalk: the machine's codebook mapped onto his

Space `lexical-v1-512`; tau_high 0.8, tau_low 0.45;
names only: no.
149 machine leaves against 117 of his.

> Compared as name + description on both sides (every leaf on both sides carries one); no fairness gap.

| band | machine leaves | what it means |
|---|---:|---|
| `same` | 0 | at or above tau_high 0.8 — the same concept |
| `grey` | 34 | between the thresholds — a live pipeline would ask the judge |
| `unmapped` | 115 | below tau_low 0.45 — nothing of his is close |

**Blind spots: 89 of his leaves nothing maps onto.**
**Inventions: 115 machine leaves with no counterpart of his.**

## Every machine leaf

`hungarian` is the one-to-one assignment over the whole vocabulary; `nearest` is the
unconstrained neighbour. They differ when a better-scoring leaf took the target first.

| machine leaf | hungarian target | score | band | nearest target | score | band |
|---|---|---:|---|---|---:|---|
| `AI-assistance_for_disabled` | - | - | - | `safety-women` | 0.308 | unmapped |
| `AI-automation_of_repetitive_tasks` | - | - | - | `positive_impacts-jobs` | 0.344 | unmapped |
| `AI-behavioral_influence` | - | - | - | `AI-omnipotence` | 0.409 | unmapped |
| `AI-complex_problem_solving` | `improvement-decision-making` | 0.518 | grey | `improvement-decision-making` | 0.518 | grey |
| `AI-creative_capability` | - | - | - | `AI-surveillance` | 0.445 | unmapped |
| `AI-daily_life_assistance` | `AI-tool` | 0.452 | grey | `AI-tool` | 0.452 | grey |
| `AI-data-driven` | - | - | - | `AI-surveillance` | 0.388 | unmapped |
| `AI-data_driven` | - | - | - | `AI-omnipotence` | 0.377 | unmapped |
| `AI-dependence-lifestyle` | - | - | - | `negative_impacts-danger_to_humans` | 0.371 | unmapped |
| `AI-disaster_management` | `key_sectors-disaster_management` | 0.593 | grey | `key_sectors-disaster_management` | 0.593 | grey |
| `AI-divine_connection` | - | - | - | `positive_impacts-autonomy` | 0.357 | unmapped |
| `AI-economic_efficiency` | - | - | - | `improvement-speed` | 0.369 | unmapped |
| `AI-economic_strengthening` | `progress-economy` | 0.710 | grey | `progress-economy` | 0.710 | grey |
| `AI-employment_transformation` | `positive_impacts-jobs` | 0.538 | grey | `positive_impacts-jobs` | 0.538 | grey |
| `AI-enhanced-communication` | - | - | - | `applications-relationships` | 0.420 | unmapped |
| `AI-entrepreneurial-support` | - | - | - | `AI-tool` | 0.399 | unmapped |
| `AI-facilitated-collaboration` | - | - | - | `negative_impacts-laziness` | 0.271 | unmapped |
| `AI-global_defence` | `key_sectors-defence` | 0.506 | grey | `key_sectors-defence` | 0.506 | grey |
| `AI-impact-immigration` | - | - | - | `positive_impacts-autonomy` | 0.468 | grey |
| `AI-impact-positive_outlook` | - | - | - | `future-positive` | 0.451 | grey |
| `AI-impact-rapid_change` | - | - | - | `improvement-future_readiness` | 0.352 | unmapped |
| `AI-impact-women_safety` | `safety-women` | 0.601 | grey | `safety-women` | 0.601 | grey |
| `AI-mindset_shift` | `adoption-necessity` | 0.465 | grey | `adoption-necessity` | 0.465 | grey |
| `AI-multi-use` | - | - | - | `AI-surveillance` | 0.415 | unmapped |
| `AI-multi_use` | - | - | - | `AI-machine_communication` | 0.397 | unmapped |
| `AI-need_for_awareness` | - | - | - | `requirements-regulation` | 0.374 | unmapped |
| `AI-omnipotence` | - | - | - | `AI-omnipotence` | 0.377 | unmapped |
| `AI-perception-central_role` | - | - | - | `future-positive` | 0.412 | unmapped |
| `AI-personalisation` | - | - | - | `improvement-personalisation` | 0.368 | unmapped |
| `AI-positive_outlook` | - | - | - | `positive_impacts-upskilling` | 0.447 | unmapped |
| `AI-productivity_enhancement` | - | - | - | `ease-work` | 0.403 | unmapped |
| `AI-robotics_engineering` | - | - | - | `positive_impacts-accessibility` | 0.443 | unmapped |
| `AI-role-expansion` | - | - | - | `AI-omnipotence` | 0.337 | unmapped |
| `AI-role-human_replacement` | - | - | - | `AI-autonomy` | 0.437 | unmapped |
| `AI-role_expansion` | - | - | - | `positive_impacts-upskilling` | 0.423 | unmapped |
| `AI-role_human_replacement` | - | - | - | `AI-self-modification` | 0.422 | unmapped |
| `AI-sector-focus-cyber_security` | - | - | - | `safety-cybersecurity` | 0.428 | unmapped |
| `AI-sector-focus-defence_education` | `key_sectors-education` | 0.475 | grey | `key_sectors-education` | 0.475 | grey |
| `AI-sector-focus-digital_marketing` | `key_sectors-marketing` | 0.599 | grey | `key_sectors-marketing` | 0.599 | grey |
| `AI-sector-focus-health` | `key_sectors-health` | 0.476 | grey | `key_sectors-health` | 0.476 | grey |
| `AI-sector-focus-transportation` | - | - | - | `progress-economy` | 0.308 | unmapped |
| `AI-sector_transformation` | - | - | - | `key_sectors-education` | 0.419 | unmapped |
| `AI-superintelligence` | `AI-superintelligence` | 0.471 | grey | `AI-superintelligence` | 0.471 | grey |
| `AI-threat-to-humanity` | - | - | - | `future-negative` | 0.453 | grey |
| `AI-transportation-autonomous_vehicles` | - | - | - | `applications-self-driving_cars` | 0.420 | unmapped |
| `AI-ubiquity` | - | - | - | `AI-surveillance` | 0.321 | unmapped |
| `AI-utility` | `applications-personal_assistant` | 0.469 | grey | `applications-personal_assistant` | 0.469 | grey |
| `accessibility-assistance_for_disabled` | - | - | - | `applications-self-driving_cars` | 0.277 | unmapped |
| `accessibility-free_healthcare` | - | - | - | `progress-now` | 0.298 | unmapped |
| `ai-dependence-lifestyle` | - | - | - | `AI-omnipotence` | 0.376 | unmapped |
| `ai-multi_use` | - | - | - | `applications-planning` | 0.405 | unmapped |
| `ai-productivity_enhancement` | - | - | - | `progress-economy` | 0.363 | unmapped |
| `ai-sector-focus-health` | - | - | - | `key_sectors-health` | 0.533 | grey |
| `ai-unclear_outputs` | - | - | - | `key_sectors-marketing` | 0.501 | grey |
| `ai-utility` | - | - | - | `AI-surveillance` | 0.371 | unmapped |
| `automation_of_repetitive_tasks` | - | - | - | `positive_impacts-automation` | 0.231 | unmapped |
| `benefit-reduced_stress` | - | - | - | `positive_impacts-stress_reduction` | 0.414 | unmapped |
| `complex_problem_solving-advance_analysis` | `positive_impacts-problem-solving` | 0.488 | grey | `positive_impacts-problem-solving` | 0.488 | grey |
| `complex_problem_solving-scientific_discovery` | - | - | - | `positive_impacts-problem-solving` | 0.269 | unmapped |
| `concern-deepfakes` | - | - | - | `applications-deep_fakes` | 0.447 | unmapped |
| `concern-ethical_development` | - | - | - | `safety-women` | 0.255 | unmapped |
| `concern-human_dependency` | - | - | - | `negative_impacts-dependency` | 0.436 | unmapped |
| `concern-privacy_security` | - | - | - | `adoption-challenges-privacy` | 0.342 | unmapped |
| `creative_capability-media_generation` | - | - | - | `requirements-informed_engagement` | 0.293 | unmapped |
| `daily_life_assistance-automated_payments` | - | - | - | `safety-privacy` | 0.390 | unmapped |
| `daily_life_assistance-automated_reminders` | - | - | - | `improvement-quality_of_life` | 0.268 | unmapped |
| `daily_life_assistance-problem_resolution` | - | - | - | `safety-privacy` | 0.351 | unmapped |
| `deepfakes` | - | - | - | `applications-deep_fakes` | 0.335 | unmapped |
| `dependence-lifestyle` | - | - | - | `ease-life` | 0.372 | unmapped |
| `economic_efficiency-productivity_gain` | - | - | - | `progress-economy` | 0.369 | unmapped |
| `economic_efficiency-recession` | - | - | - | `negative_impacts-misuse` | 0.422 | unmapped |
| `economic_impact-productivity_gain` | - | - | - | `progress-economy` | 0.352 | unmapped |
| `economic_impact-universal_basic_income` | `requirements-basic_income` | 0.496 | grey | `requirements-basic_income` | 0.496 | grey |
| `education-accessibility` | - | - | - | `key_sectors-education` | 0.331 | unmapped |
| `education-literacy_requirement` | - | - | - | `AI-surveillance` | 0.328 | unmapped |
| `education-personalised_learning` | - | - | - | `AI-tool` | 0.316 | unmapped |
| `education-sector-transformation` | - | - | - | `key_sectors-education` | 0.360 | unmapped |
| `education-sector_transformation` | - | - | - | `key_sectors-education` | 0.406 | unmapped |
| `employment_transformation-job_creation` | - | - | - | `positive_impacts-jobs` | 0.392 | unmapped |
| `employment_transformation-job_displacement` | - | - | - | `negative_impacts-job_destruction` | 0.441 | unmapped |
| `employment_transformation-job_transformation` | - | - | - | `negative_impacts-job_destruction` | 0.327 | unmapped |
| `employment_transformation-remote_work` | - | - | - | `future-inevitability` | 0.266 | unmapped |
| `employment_transformation-workforce_retraining` | - | - | - | `positive_impacts-productivity` | 0.298 | unmapped |
| `enhanced-communication` | - | - | - | `negative_impacts-danger_to_humans` | 0.311 | unmapped |
| `facilitated-collaboration` | - | - | - | `negative_impacts-dependency` | 0.356 | unmapped |
| `global_defence` | - | - | - | `key_sectors-entertainment` | 0.290 | unmapped |
| `impact-communication_enhancement` | - | - | - | `negative_impacts-lack_of_information` | 0.312 | unmapped |
| `impact-digital_connectivity` | - | - | - | `applications-relationships` | 0.298 | unmapped |
| `impact-digital_exclusion` | - | - | - | `negative_impacts-danger_to_humans` | 0.456 | grey |
| `impact-enhanced-communication` | `positive_impacts-upskilling` | 0.481 | grey | `positive_impacts-upskilling` | 0.481 | grey |
| `impact-public_safety` | - | - | - | `key_sectors-disaster_management` | 0.439 | unmapped |
| `impact-rapid_change` | - | - | - | `impact-climate_change` | 0.329 | unmapped |
| `impact-technological_advancement` | - | - | - | `progress-holistic` | 0.402 | unmapped |
| `impact-work_ease` | - | - | - | `ease-work` | 0.385 | unmapped |
| `job_displacement` | - | - | - | `negative_impacts-job_destruction` | 0.423 | unmapped |
| `labor-competitive_advantage` | - | - | - | `adoption-present` | 0.324 | unmapped |
| `labor-free_workforce` | `positive_impacts-productivity` | 0.466 | grey | `positive_impacts-productivity` | 0.466 | grey |
| `labor-job_transformation` | - | - | - | `impact-jobs` | 0.400 | unmapped |
| `mindset_shift-problem_identification` | - | - | - | `positive_impacts-problem-solving` | 0.288 | unmapped |
| `multi-use` | - | - | - | `positive_impacts-productivity` | 0.276 | unmapped |
| `multi_use` | - | - | - | `applications-navigation` | 0.375 | unmapped |
| `need_for_awareness-literacy` | - | - | - | `AI-tool` | 0.292 | unmapped |
| `negative_impacts-cybersecurity_risks` | - | - | - | `positive_impacts-drug_discovery` | 0.232 | unmapped |
| `negative_impacts-dual_nature` | - | - | - | `negative_impacts-general` | 0.371 | unmapped |
| `negative_impacts-human_subjugation` | - | - | - | `negative_impacts-danger_to_humans` | 0.517 | grey |
| `negative_impacts-job_destruction` | `negative_impacts-job_destruction` | 0.547 | grey | `negative_impacts-job_destruction` | 0.547 | grey |
| `negative_impacts-laziness` | `negative_impacts-laziness` | 0.545 | grey | `negative_impacts-laziness` | 0.545 | grey |
| `negative_impacts-misuse` | `negative_impacts-misuse` | 0.579 | grey | `negative_impacts-misuse` | 0.579 | grey |
| `negative_impacts-physical_health` | `negative_impacts-danger_to_humans` | 0.523 | grey | `negative_impacts-danger_to_humans` | 0.523 | grey |
| `perception-central_role` | - | - | - | `applications-relationships` | 0.352 | unmapped |
| `perception-fleeting_trend` | - | - | - | `improvement-decision-making` | 0.263 | unmapped |
| `perception-technological_luck` | - | - | - | `ease-life` | 0.302 | unmapped |
| `personalisation-style_suggestions` | - | - | - | `requirements-regulation` | 0.265 | unmapped |
| `personalisation-virtual_trials` | - | - | - | `applications-simulation` | 0.441 | unmapped |
| `positive_outcomes-accessible_healthcare` | `positive_impacts-accessibility` | 0.510 | grey | `positive_impacts-accessibility` | 0.510 | grey |
| `positive_outcomes-work_relief` | `ease-work` | 0.458 | grey | `ease-work` | 0.458 | grey |
| `positive_outlook-wealth_and_happiness` | - | - | - | `future-positive` | 0.405 | unmapped |
| `positive_outlook-work_relief` | - | - | - | `positive_impacts-productivity` | 0.362 | unmapped |
| `privacy_security-safe_sharing` | - | - | - | `safety-privacy` | 0.384 | unmapped |
| `resource-efficiency` | - | - | - | `applications-information` | 0.322 | unmapped |
| `robotics_engineering` | - | - | - | `positive_impacts-automation` | 0.338 | unmapped |
| `role_human_replacement` | - | - | - | `AI-superintelligence` | 0.382 | unmapped |
| `safety-human_safety` | - | - | - | `safety-women` | 0.423 | unmapped |
| `safety-improvements-shelter_security` | - | - | - | `safety-home` | 0.399 | unmapped |
| `safety-kill_switch` | - | - | - | `safety-women` | 0.275 | unmapped |
| `safety-reduced_accidents` | - | - | - | `negative_impacts-enslavement` | 0.316 | unmapped |
| `safety_improvements` | - | - | - | `safety-women` | 0.217 | unmapped |
| `sector-focus-cyber_security` | `safety-cybersecurity` | 0.502 | grey | `safety-cybersecurity` | 0.502 | grey |
| `sector-focus-digital_marketing` | - | - | - | `key_sectors-marketing` | 0.523 | grey |
| `sector-focus-education` | - | - | - | `key_sectors-education` | 0.426 | unmapped |
| `sector-focus-health` | - | - | - | `key_sectors-health` | 0.453 | grey |
| `sector-focus-hospitality` | - | - | - | `key_sectors-entertainment` | 0.277 | unmapped |
| `sector-focus-programming` | - | - | - | `AI-tool` | 0.353 | unmapped |
| `sector-focus-real_estate` | - | - | - | `key_sectors-technology` | 0.285 | unmapped |
| `sector-focus-transportation` | - | - | - | `future-transformation` | 0.312 | unmapped |
| `sector_transformation` | - | - | - | `future-transformation` | 0.435 | unmapped |
| `security-cyber_security` | - | - | - | `safety-cybersecurity` | 0.327 | unmapped |
| `society-digital-transformation` | - | - | - | `positive_impacts-invention` | 0.205 | unmapped |
| `society-social_norms` | - | - | - | `negative_impacts-general` | 0.162 | unmapped |
| `threat-to-humanity` | - | - | - | `future-negative` | 0.396 | unmapped |
| `transport_automation` | - | - | - | `key_sectors-transport` | 0.279 | unmapped |
| `transportation-autonomous_vehicles` | `applications-self-driving_cars` | 0.464 | grey | `applications-self-driving_cars` | 0.464 | grey |
| `transportation-navigation_assistance` | - | - | - | `applications-navigation` | 0.378 | unmapped |
| `ubiquity` | - | - | - | `progress-holistic` | 0.354 | unmapped |
| `unclear_outputs` | - | - | - | `key_sectors-marketing` | 0.327 | unmapped |
| `user_experience_relaxation` | - | - | - | `positive_impacts-greater_enjoyment` | 0.365 | unmapped |
| `utility-work_ease` | - | - | - | `ease-work` | 0.395 | unmapped |
| `utility-work_efficiency` | - | - | - | `efficiency` | 0.404 | unmapped |
| `workforce_retraining` | - | - | - | `AI-tool` | 0.367 | unmapped |

## His families, and where the machine's leaves land

| his family | his leaves | machine leaves landing here | from machine families | blind spots |
|---|---:|---:|---|---:|
| `AI` | 8 | 2 | `AI` 2 | 6 |
| `adoption` | 6 | 1 | `AI` 1 | 5 |
| `applications` | 22 | 2 | `AI` 1, `transportation` 1 | 20 |
| `ease` | 3 | 1 | `positive_outcomes` 1 | 2 |
| `efficiency` | 1 | 0 | - | 1 |
| `future` | 5 | 2 | `AI` 2 | 3 |
| `impact` | 6 | 0 | - | 6 |
| `improvement` | 8 | 1 | `AI` 1 | 7 |
| `jobs` | 6 | 0 | - | 6 |
| `key_sectors` | 11 | 9 | `AI` 5, `ai` 2, `sector` 2 | 6 |
| `negative_impacts` | 13 | 6 | `impact` 1, `negative_impacts` 5 | 9 |
| `positive_impacts` | 16 | 6 | `AI` 2, `complex_problem_solving` 1, `impact` 1, `labor` 1, `positive_outcomes` 1 | 10 |
| `progress` | 3 | 1 | `AI` 1 | 2 |
| `requirements` | 4 | 1 | `economic_impact` 1 | 3 |
| `safety` | 5 | 2 | `AI` 1, `sector` 1 | 3 |

## The machine's families, and where they land in his tree

| machine family | leaves | lands in | scattered | unmapped |
|---|---:|---|---|---:|
| `AI` | 47 | `AI` 2, `adoption` 1, `applications` 1, `future` 2, `improvement` 1, `key_sectors` 5, `positive_impacts` 2, `progress` 1, `safety` 1 | yes | 31 |
| `accessibility` | 2 | - | no | 2 |
| `ai` | 6 | `key_sectors` 2 | no | 4 |
| `automation_of_repetitive_tasks` | 1 | - | no | 1 |
| `benefit` | 1 | - | no | 1 |
| `complex_problem_solving` | 2 | `positive_impacts` 1 | no | 1 |
| `concern` | 4 | - | no | 4 |
| `creative_capability` | 1 | - | no | 1 |
| `daily_life_assistance` | 3 | - | no | 3 |
| `deepfakes` | 1 | - | no | 1 |
| `dependence` | 1 | - | no | 1 |
| `economic_efficiency` | 2 | - | no | 2 |
| `economic_impact` | 2 | `requirements` 1 | no | 1 |
| `education` | 5 | - | no | 5 |
| `employment_transformation` | 5 | - | no | 5 |
| `enhanced` | 1 | - | no | 1 |
| `facilitated` | 1 | - | no | 1 |
| `global_defence` | 1 | - | no | 1 |
| `impact` | 8 | `negative_impacts` 1, `positive_impacts` 1 | yes | 6 |
| `job_displacement` | 1 | - | no | 1 |
| `labor` | 3 | `positive_impacts` 1 | no | 2 |
| `mindset_shift` | 1 | - | no | 1 |
| `multi` | 1 | - | no | 1 |
| `multi_use` | 1 | - | no | 1 |
| `need_for_awareness` | 1 | - | no | 1 |
| `negative_impacts` | 7 | `negative_impacts` 5 | no | 2 |
| `perception` | 3 | - | no | 3 |
| `personalisation` | 2 | - | no | 2 |
| `positive_outcomes` | 2 | `ease` 1, `positive_impacts` 1 | yes | 0 |
| `positive_outlook` | 2 | - | no | 2 |
| `privacy_security` | 1 | - | no | 1 |
| `resource` | 1 | - | no | 1 |
| `robotics_engineering` | 1 | - | no | 1 |
| `role_human_replacement` | 1 | - | no | 1 |
| `safety` | 4 | - | no | 4 |
| `safety_improvements` | 1 | - | no | 1 |
| `sector` | 8 | `key_sectors` 2, `safety` 1 | yes | 5 |
| `sector_transformation` | 1 | - | no | 1 |
| `security` | 1 | - | no | 1 |
| `society` | 2 | - | no | 2 |
| `threat` | 1 | - | no | 1 |
| `transport_automation` | 1 | - | no | 1 |
| `transportation` | 2 | `applications` 1 | no | 1 |
| `ubiquity` | 1 | - | no | 1 |
| `unclear_outputs` | 1 | - | no | 1 |
| `user_experience_relaxation` | 1 | - | no | 1 |
| `utility` | 2 | - | no | 2 |
| `workforce_retraining` | 1 | - | no | 1 |

### Blind spots — his leaves nothing maps onto

`AI-autonomy`, `AI-machine_communication`, `AI-omnipotence`, `AI-self-modification`, `AI-speed`, `AI-surveillance`, `adoption-challenges-job_losses`, `adoption-challenges-privacy`, `adoption-challenges-safety`, `adoption-high`, `adoption-present`, `applications-chatbots`, `applications-decision-making`, `applications-deep_fakes`, `applications-financial_assistance`, `applications-friend`, `applications-information`, `applications-medical_care`, `applications-meetings`, `applications-navigation`, `applications-planning`, `applications-problem-solving`, `applications-relationships`, `applications-research`, `applications-robotics`, `applications-search`, `applications-simulation`, `applications-summarising`, `applications-text_generation`, `applications-translation`, `applications-voice_recognition`, `ease-life`, `ease-travel`, `efficiency`, `future-hazard_avoidance`, `future-inevitability`, `future-transformation`, `impact-climate_change`, `impact-context-specific`, `impact-global`, `impact-jobs`, `impact-misconception`, `impact-travel_immigration`, `improvement-accuracy`, `improvement-future_readiness`, `improvement-health`, `improvement-personalisation`, `improvement-quality_of_life`, `improvement-speed`, `improvement-teaching_learning`, `jobs-businessman`, `jobs-computer_operator`, `jobs-driver`, `jobs-nurse`, `jobs-surveillance`, `jobs-tutor`, `key_sectors-elder_care`, `key_sectors-entertainment`, `key_sectors-finance`, `key_sectors-manufacturing`, `key_sectors-technology`, `key_sectors-transport`, `negative_impacts-control`, `negative_impacts-dependency`, `negative_impacts-deskilling`, `negative_impacts-domination`, `negative_impacts-enslavement`, `negative_impacts-general`, `negative_impacts-immobility`, `negative_impacts-lack_of_inclusion`, `negative_impacts-lack_of_information`, `positive_impacts-automation`, `positive_impacts-corruption_reduction`, `positive_impacts-cost_reduction`, `positive_impacts-drug_discovery`, `positive_impacts-general`, `positive_impacts-greater_enjoyment`, `positive_impacts-health`, `positive_impacts-invention`, `positive_impacts-personalisation`, `positive_impacts-stress_reduction`, `progress-holistic`, `progress-now`, `requirements-informed_engagement`, `requirements-oversight`, `requirements-regulation`, `safety-home`, `safety-privacy`, `safety-travel`

### Inventions — machine leaves with no counterpart of his

`AI-assistance_for_disabled`, `AI-automation_of_repetitive_tasks`, `AI-behavioral_influence`, `AI-creative_capability`, `AI-data-driven`, `AI-data_driven`, `AI-dependence-lifestyle`, `AI-divine_connection`, `AI-economic_efficiency`, `AI-enhanced-communication`, `AI-entrepreneurial-support`, `AI-facilitated-collaboration`, `AI-impact-rapid_change`, `AI-multi-use`, `AI-multi_use`, `AI-need_for_awareness`, `AI-omnipotence`, `AI-perception-central_role`, `AI-personalisation`, `AI-positive_outlook`, `AI-productivity_enhancement`, `AI-robotics_engineering`, `AI-role-expansion`, `AI-role-human_replacement`, `AI-role_expansion`, `AI-role_human_replacement`, `AI-sector-focus-cyber_security`, `AI-sector-focus-transportation`, `AI-sector_transformation`, `AI-transportation-autonomous_vehicles`, `AI-ubiquity`, `accessibility-assistance_for_disabled`, `accessibility-free_healthcare`, `ai-dependence-lifestyle`, `ai-multi_use`, `ai-productivity_enhancement`, `ai-utility`, `automation_of_repetitive_tasks`, `benefit-reduced_stress`, `complex_problem_solving-scientific_discovery`, `concern-deepfakes`, `concern-ethical_development`, `concern-human_dependency`, `concern-privacy_security`, `creative_capability-media_generation`, `daily_life_assistance-automated_payments`, `daily_life_assistance-automated_reminders`, `daily_life_assistance-problem_resolution`, `deepfakes`, `dependence-lifestyle`, `economic_efficiency-productivity_gain`, `economic_efficiency-recession`, `economic_impact-productivity_gain`, `education-accessibility`, `education-literacy_requirement`, `education-personalised_learning`, `education-sector-transformation`, `education-sector_transformation`, `employment_transformation-job_creation`, `employment_transformation-job_displacement`, `employment_transformation-job_transformation`, `employment_transformation-remote_work`, `employment_transformation-workforce_retraining`, `enhanced-communication`, `facilitated-collaboration`, `global_defence`, `impact-communication_enhancement`, `impact-digital_connectivity`, `impact-public_safety`, `impact-rapid_change`, `impact-technological_advancement`, `impact-work_ease`, `job_displacement`, `labor-competitive_advantage`, `labor-job_transformation`, `mindset_shift-problem_identification`, `multi-use`, `multi_use`, `need_for_awareness-literacy`, `negative_impacts-cybersecurity_risks`, `negative_impacts-dual_nature`, `perception-central_role`, `perception-fleeting_trend`, `perception-technological_luck`, `personalisation-style_suggestions`, `personalisation-virtual_trials`, `positive_outlook-wealth_and_happiness`, `positive_outlook-work_relief`, `privacy_security-safe_sharing`, `resource-efficiency`, `robotics_engineering`, `role_human_replacement`, `safety-human_safety`, `safety-improvements-shelter_security`, `safety-kill_switch`, `safety-reduced_accidents`, `safety_improvements`, `sector-focus-education`, `sector-focus-hospitality`, `sector-focus-programming`, `sector-focus-real_estate`, `sector-focus-transportation`, `sector_transformation`, `security-cyber_security`, `society-digital-transformation`, `society-social_norms`, `threat-to-humanity`, `transport_automation`, `transportation-navigation_assistance`, `ubiquity`, `unclear_outputs`, `user_experience_relaxation`, `utility-work_ease`, `utility-work_efficiency`, `workforce_retraining`
