# 06 - Concurrent validation: his coding against the machine's

The machine side here is a pair of live models served on this machine (the run's own
config names them), a weaker pair than the approved line-up. Agreement here tests the
pipeline; it is not what the approved models would find.

## Descriptions on both sides

Embedding space `local-embeddinggemma-768`, tau_high 0.8: 4 of 71 human codes matched to one of 56 machine codes.

| scope | precision | recall | F1 | kappa | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| all codes (union vocabulary) | 0.052 | 0.048 | 0.050 | -0.010 | 7 | 127 | 139 |
| matched codes only | 0.583 | 1.000 | 0.737 | 0.702 | 7 | 5 | 0 |

| segment level | precision | recall | F1 |
|---|---:|---:|---:|
| span-overlap weighted | 0.025 | 0.025 | 0.025 |
| strict (overlap >= 0.5) | 0.024 | 0.024 | 0.024 |

Right code, wrong place: 5; mean overlap on shared codes 0.469.

### Code matching (Hungarian assignment, nearest pairs)

| human code | machine code | similarity | accepted |
|---|---|---:|---|
| `AI-superintelligence` | `AI-superintelligence` | 1.000 | yes |
| `negative_impacts-job_destruction` | `negative_impacts-job_destruction` | 1.000 | yes |
| `negative_impacts-misuse` | `negative_impacts-misuse` | 1.000 | yes |
| `positive_impacts-stress_reduction` | `benefit-reduced_stress` | 0.805 | yes |
| `future-positive` | `positive_outlook` | 0.785 | no |
| `applications-simulation` | `personalisation-virtual_trials` | 0.766 | no |
| `negative_impacts-danger_to_humans` | `AI-threat-to-humanity` | 0.765 | no |
| `key_sectors-health` | `AI-sector-focus-health` | 0.762 | no |
| `negative_impacts-dependency` | `concern-human_dependency` | 0.759 | no |
| `negative_impacts-enslavement` | `negative_impacts-human_subjugation` | 0.748 | no |
| `positive_impacts-jobs` | `AI-employment_transformation` | 0.739 | no |
| `negative_impacts-immobility` | `negative_impacts-laziness` | 0.738 | no |
| `adoption-necessity` | `AI-mindset_shift` | 0.736 | no |
| `impact-jobs` | `labor-job_transformation` | 0.734 | no |
| `ease-work` | `impact-work_ease` | 0.722 | no |
| `safety-cybersecurity` | `sector-focus-cyber_security` | 0.722 | no |
| `progress-holistic` | `impact-technological_advancement` | 0.715 | no |
| `positive_impacts-productivity` | `economic_impact-productivity_gain` | 0.715 | no |
| `ease-travel` | `user_experience_relaxation` | 0.707 | no |
| `future-transformation` | `sector_transformation` | 0.706 | no |
| `positive_impacts-personalisation` | `personalisation` | 0.695 | no |
| `positive_impacts-cost_reduction` | `AI-economic_efficiency` | 0.690 | no |
| `applications-self-driving_cars` | `transportation-autonomous_vehicles` | 0.672 | no |
| `negative_impacts-lack_of_information` | `impact-digital_exclusion` | 0.670 | no |
| `future-hazard_avoidance` | `concern-ethical_development` | 0.661 | no |
| `adoption-high` | `ubiquity` | 0.658 | no |
| `positive_impacts-upskilling` | `AI-role_expansion` | 0.647 | no |
| `adoption-present` | `AI-ubiquity` | 0.645 | no |
| `future-negative` | `concern-misuse` | 0.643 | no |
| `positive_impacts-automation` | `positive_outcomes-work_relief` | 0.632 | no |
| `improvement-quality_of_life` | `daily_life_assistance-problem_resolution` | 0.625 | no |
| `applications-deep_fakes` | `concern-deepfakes` | 0.624 | no |
| `ease-life` | `ai-productivity_enhancement` | 0.619 | no |
| `requirements-basic_income` | `economic_impact-universal_basic_income` | 0.615 | no |
| `applications-problem-solving` | `daily_life_assistance` | 0.611 | no |
| `applications-friend` | `AI-multi-use` | 0.604 | no |
| `positive_impacts-problem-solving` | `complex_problem_solving` | 0.603 | no |
| `improvement-future_readiness` | `complex_problem_solving-advance_analysis` | 0.599 | no |
| `positive_impacts-general` | `AI-positive_outlook` | 0.595 | no |
| `applications-personal_assistant` | `AI-role-expansion` | 0.592 | no |
| `applications-chatbots` | `AI-daily_life_assistance` | 0.592 | no |
| `improvement-accuracy` | `AI-productivity_enhancement` | 0.586 | no |
| `AI-autonomy` | `AI-omnipotence` | 0.585 | no |
| `AI-speed` | `utility-work_efficiency` | 0.580 | no |
| `applications-medical_care` | `ai-utility` | 0.578 | no |
| `AI-machine_communication` | `AI-enhanced-communication` | 0.570 | no |
| `safety-home` | `safety-improvements-shelter_security` | 0.566 | no |
| `negative_impacts-domination` | `ai-dependence-lifestyle` | 0.546 | no |
| `applications-planning` | `AI-automation_of_repetitive_tasks` | 0.535 | no |
| `applications-decision-making` | `accessibility-free_healthcare` | 0.498 | no |
| `impact-misconception` | `AI-role-human_replacement` | 0.491 | no |
| `applications-information` | `impact-communication_enhancement` | 0.490 | no |
| `improvement-personalisation` | `labor-competitive_advantage` | 0.474 | no |
| `future-inevitability` | `AI-perception-central_role` | 0.459 | no |
| `impact-global` | `society-digital-transformation` | 0.415 | no |
| `AI-self-modification` | `automation_of_repetitive_tasks` | 0.408 | no |

### Over-coding - machine codes with no human counterpart (52 codes, 153 segments)

| machine code | segments | responses | nearest human code | cosine |
|---|---:|---|---|---:|
| `AI-automation_of_repetitive_tasks` | 5 | 45, 51, 52, 81 | `ease-work` | 0.645 |
| `AI-daily_life_assistance` | 4 | 52, 53, 84 | `applications-chatbots` | 0.592 |
| `AI-economic_efficiency` | 1 | 47 | `positive_impacts-cost_reduction` | 0.690 |
| `AI-employment_transformation` | 4 | 45, 64, 81 | `positive_impacts-jobs` | 0.739 |
| `AI-enhanced-communication` | 5 | 43, 67, 81, 84 | `applications-friend` | 0.618 |
| `AI-mindset_shift` | 1 | 64 | `adoption-necessity` | 0.736 |
| `AI-multi-use` | 8 | 45, 51, 52, 53, 73, 81, 82 | `applications-friend` | 0.604 |
| `AI-omnipotence` | 3 | 67, 84 | `negative_impacts-danger_to_humans` | 0.618 |
| `AI-perception-central_role` | 4 | 47, 52, 236 | `future-transformation` | 0.537 |
| `AI-positive_outlook` | 5 | 43, 46, 73 | `positive_impacts-jobs` | 0.626 |
| `AI-productivity_enhancement` | 9 | 45, 46, 51, 53, 81, 90, 138 | `ease-work` | 0.658 |
| `AI-role-expansion` | 1 | 67 | `applications-personal_assistant` | 0.592 |
| `AI-role-human_replacement` | 5 | 47, 51, 52, 80 | `negative_impacts-enslavement` | 0.573 |
| `AI-role_expansion` | 1 | 138 | `positive_impacts-upskilling` | 0.647 |
| `AI-sector-focus-health` | 2 | 88 | `key_sectors-health` | 0.762 |
| `AI-threat-to-humanity` | 1 | 100 | `negative_impacts-danger_to_humans` | 0.765 |
| `AI-ubiquity` | 10 | 43, 51, 53, 64, 80, 82, 90, 138 | `adoption-high` | 0.692 |
| `accessibility-free_healthcare` | 1 | 88 | `positive_impacts-cost_reduction` | 0.531 |
| `ai-dependence-lifestyle` | 6 | 64, 80, 84, 236 | `negative_impacts-dependency` | 0.698 |
| `ai-productivity_enhancement` | 1 | 90 | `ease-life` | 0.619 |
| `ai-utility` | 4 | 81, 84, 138 | `applications-personal_assistant` | 0.658 |
| `automation_of_repetitive_tasks` | 1 | 53 | `positive_impacts-automation` | 0.453 |
| `complex_problem_solving` | 2 | 82 | `positive_impacts-problem-solving` | 0.603 |
| `complex_problem_solving-advance_analysis` | 1 | 88 | `positive_impacts-problem-solving` | 0.614 |
| `concern-deepfakes` | 1 | 73 | `applications-deep_fakes` | 0.624 |
| `concern-ethical_development` | 3 | 67, 73 | `future-hazard_avoidance` | 0.661 |
| `concern-human_dependency` | 8 | 46, 67, 80, 100, 236 | `negative_impacts-dependency` | 0.759 |
| `concern-misuse` | 2 | 236 | `negative_impacts-danger_to_humans` | 0.672 |
| `daily_life_assistance` | 4 | 82, 90 | `applications-problem-solving` | 0.611 |
| `daily_life_assistance-problem_resolution` | 1 | 88 | `applications-problem-solving` | 0.630 |
| `economic_impact-productivity_gain` | 1 | 138 | `positive_impacts-productivity` | 0.715 |
| `economic_impact-universal_basic_income` | 1 | 47 | `requirements-basic_income` | 0.615 |
| `impact-communication_enhancement` | 1 | 53 | `applications-information` | 0.490 |
| `impact-digital_exclusion` | 1 | 100 | `negative_impacts-lack_of_information` | 0.670 |
| `impact-technological_advancement` | 5 | 43, 64, 73, 82, 90 | `progress-holistic` | 0.715 |
| `impact-work_ease` | 4 | 43, 45, 81 | `ease-work` | 0.722 |
| `labor-competitive_advantage` | 1 | 64 | `positive_impacts-productivity` | 0.558 |
| `labor-job_transformation` | 3 | 47, 51, 138 | `impact-jobs` | 0.734 |
| `negative_impacts-human_subjugation` | 1 | 100 | `negative_impacts-enslavement` | 0.748 |
| `negative_impacts-laziness` | 3 | 46, 80 | `negative_impacts-immobility` | 0.738 |
| `personalisation` | 1 | 81 | `positive_impacts-personalisation` | 0.695 |
| `personalisation-virtual_trials` | 1 | 90 | `applications-simulation` | 0.766 |
| `positive_outcomes-work_relief` | 6 | 45, 46, 47, 81, 236 | `positive_impacts-stress_reduction` | 0.732 |
| `positive_outlook` | 10 | 52, 53, 64, 82, 84, 88, 90, 138, 236 | `future-positive` | 0.785 |
| `safety-improvements-shelter_security` | 1 | 52 | `safety-home` | 0.566 |
| `sector-focus-cyber_security` | 1 | 81 | `safety-cybersecurity` | 0.722 |
| `sector_transformation` | 1 | 51 | `future-transformation` | 0.706 |
| `society-digital-transformation` | 1 | 80 | `future-transformation` | 0.519 |
| `transportation-autonomous_vehicles` | 2 | 51 | `applications-self-driving_cars` | 0.672 |
| `ubiquity` | 1 | 236 | `adoption-high` | 0.658 |
| `user_experience_relaxation` | 1 | 81 | `ease-travel` | 0.707 |
| `utility-work_efficiency` | 2 | 45, 73 | `ease-work` | 0.655 |

### Blind spots - human codes the machine never produced (67 codes, 161 segments)

The only place the negative example "you did not generate a new code" is observable:
a code never invented leaves no artefact inside a run. The segments themselves are in
the local run directory's `agreement.md`.

| human code | segments | responses | nearest machine code | cosine |
|---|---:|---|---|---:|
| `AI-autonomy` | 2 | 67, 100 | `AI-omnipotence` | 0.585 |
| `AI-machine_communication` | 1 | 67 | `AI-superintelligence` | 0.591 |
| `AI-self-modification` | 1 | 67 | `AI-omnipotence` | 0.561 |
| `AI-speed` | 1 | 67 | `economic_impact-productivity_gain` | 0.595 |
| `adoption-high` | 5 | 51, 53, 82, 138, 236 | `AI-ubiquity` | 0.692 |
| `adoption-necessity` | 2 | 64 | `AI-mindset_shift` | 0.736 |
| `adoption-present` | 4 | 43, 64, 138 | `AI-ubiquity` | 0.645 |
| `applications-chatbots` | 2 | 53, 81 | `AI-daily_life_assistance` | 0.592 |
| `applications-decision-making` | 1 | 82 | `daily_life_assistance` | 0.558 |
| `applications-deep_fakes` | 1 | 73 | `concern-deepfakes` | 0.624 |
| `applications-friend` | 5 | 43, 82, 84 | `AI-enhanced-communication` | 0.618 |
| `applications-information` | 1 | 138 | `utility-work_efficiency` | 0.503 |
| `applications-medical_care` | 1 | 52 | `ai-utility` | 0.578 |
| `applications-meetings` | 2 | 43, 45 | `ai-utility` | 0.560 |
| `applications-personal_assistant` | 2 | 81, 84 | `ai-utility` | 0.658 |
| `applications-planning` | 1 | 45 | `utility-work_efficiency` | 0.580 |
| `applications-problem-solving` | 2 | 84, 138 | `daily_life_assistance-problem_resolution` | 0.630 |
| `applications-robotics` | 4 | 51, 52, 80 | `utility-work_efficiency` | 0.500 |
| `applications-search` | 4 | 45, 80, 81, 90 | `personalisation-virtual_trials` | 0.556 |
| `applications-self-driving_cars` | 1 | 51 | `transportation-autonomous_vehicles` | 0.672 |
| `applications-simulation` | 1 | 90 | `personalisation-virtual_trials` | 0.766 |
| `applications-summarising` | 2 | 81, 90 | `personalisation` | 0.542 |
| `applications-text_generation` | 1 | 45 | `utility-work_efficiency` | 0.500 |
| `applications-voice_recognition` | 1 | 81 | `ai-utility` | 0.551 |
| `ease-life` | 8 | 43, 51, 53, 81, 84, 90 | `ai-utility` | 0.621 |
| `ease-travel` | 1 | 53 | `user_experience_relaxation` | 0.707 |
| `ease-work` | 7 | 43, 45, 46, 81 | `impact-work_ease` | 0.722 |
| `efficiency` | 5 | 45, 46, 73, 81, 138 | `utility-work_efficiency` | 0.576 |
| `future-hazard_avoidance` | 2 | 67, 73 | `concern-ethical_development` | 0.661 |
| `future-inevitability` | 5 | 43, 47, 51, 64, 138 | `AI-omnipotence` | 0.566 |
| `future-negative` | 2 | 73, 100 | `negative_impacts-human_subjugation` | 0.678 |
| `future-positive` | 7 | 45, 52, 53, 64, 84, 88 | `positive_outlook` | 0.785 |
| `future-transformation` | 5 | 51, 64, 81, 82, 90 | `sector_transformation` | 0.706 |
| `impact-global` | 2 | 47, 90 | `sector_transformation` | 0.588 |
| `impact-jobs` | 4 | 47, 51, 73 | `negative_impacts-job_destruction` | 0.740 |
| `impact-misconception` | 1 | 82 | `AI-mindset_shift` | 0.554 |
| `improvement-accuracy` | 3 | 51, 73, 84 | `AI-productivity_enhancement` | 0.586 |
| `improvement-future_readiness` | 1 | 88 | `complex_problem_solving-advance_analysis` | 0.599 |
| `improvement-personalisation` | 1 | 90 | `personalisation` | 0.693 |
| `improvement-quality_of_life` | 2 | 52, 88 | `daily_life_assistance-problem_resolution` | 0.625 |
| `jobs-computer_operator` | 1 | 51 | `utility-work_efficiency` | 0.398 |
| `jobs-nurse` | 1 | 52 | `safety-improvements-shelter_security` | 0.418 |
| `key_sectors-elder_care` | 2 | 52 | `AI-sector-focus-health` | 0.475 |
| `key_sectors-health` | 2 | 47, 88 | `AI-sector-focus-health` | 0.762 |
| `negative_impacts-danger_to_humans` | 2 | 67, 73 | `AI-threat-to-humanity` | 0.765 |
| `negative_impacts-dependency` | 4 | 46, 64, 80, 100 | `concern-human_dependency` | 0.759 |
| `negative_impacts-deskilling` | 3 | 46, 80 | `negative_impacts-laziness` | 0.656 |
| `negative_impacts-domination` | 1 | 80 | `negative_impacts-human_subjugation` | 0.688 |
| `negative_impacts-enslavement` | 3 | 46, 67, 100 | `negative_impacts-human_subjugation` | 0.748 |
| `negative_impacts-general` | 2 | 46, 73 | `negative_impacts-job_destruction` | 0.610 |
| `negative_impacts-immobility` | 1 | 80 | `negative_impacts-laziness` | 0.738 |
| `negative_impacts-lack_of_information` | 2 | 80, 100 | `impact-digital_exclusion` | 0.670 |
| `positive_impacts-automation` | 3 | 51, 53, 81 | `benefit-reduced_stress` | 0.632 |
| `positive_impacts-cost_reduction` | 1 | 88 | `AI-economic_efficiency` | 0.690 |
| `positive_impacts-general` | 9 | 46, 64, 73, 88 | `AI-positive_outlook` | 0.595 |
| `positive_impacts-health` | 1 | 88 | `benefit-reduced_stress` | 0.463 |
| `positive_impacts-jobs` | 1 | 64 | `AI-employment_transformation` | 0.739 |
| `positive_impacts-personalisation` | 1 | 81 | `personalisation` | 0.695 |
| `positive_impacts-problem-solving` | 7 | 81, 82, 88, 90, 138 | `AI-productivity_enhancement` | 0.633 |
| `positive_impacts-productivity` | 1 | 138 | `economic_impact-productivity_gain` | 0.715 |
| `positive_impacts-upskilling` | 1 | 138 | `AI-role_expansion` | 0.647 |
| `progress-holistic` | 1 | 43 | `impact-technological_advancement` | 0.715 |
| `requirements-basic_income` | 1 | 47 | `economic_impact-universal_basic_income` | 0.615 |
| `requirements-regulation` | 3 | 46, 73 | `concern-ethical_development` | 0.569 |
| `safety-cybersecurity` | 1 | 81 | `sector-focus-cyber_security` | 0.722 |
| `safety-home` | 1 | 52 | `sector-focus-cyber_security` | 0.592 |
| `safety-privacy` | 1 | 81 | `sector-focus-cyber_security` | 0.607 |

## Name against name: no descriptions on either side

Embedding space `local-embeddinggemma-768`, tau_high 0.8: 7 of 71 human codes matched to one of 56 machine codes.

| scope | precision | recall | F1 | kappa | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| all codes (union vocabulary) | 0.075 | 0.068 | 0.071 | 0.011 | 10 | 124 | 136 |
| matched codes only | 0.526 | 0.714 | 0.606 | 0.552 | 10 | 9 | 4 |

| segment level | precision | recall | F1 |
|---|---:|---:|---:|
| span-overlap weighted | 0.029 | 0.029 | 0.029 |
| strict (overlap >= 0.5) | 0.030 | 0.029 | 0.030 |

Right code, wrong place: 7; mean overlap on shared codes 0.405.

### Code matching (Hungarian assignment, nearest pairs)

| human code | machine code | similarity | accepted |
|---|---|---:|---|
| `AI-superintelligence` | `AI-superintelligence` | 1.000 | yes |
| `negative_impacts-job_destruction` | `negative_impacts-job_destruction` | 1.000 | yes |
| `negative_impacts-misuse` | `negative_impacts-misuse` | 1.000 | yes |
| `improvement-personalisation` | `personalisation` | 0.847 | yes |
| `AI-machine_communication` | `AI-enhanced-communication` | 0.842 | yes |
| `positive_impacts-productivity` | `economic_impact-productivity_gain` | 0.805 | yes |
| `efficiency` | `utility-work_efficiency` | 0.801 | yes |
| `future-positive` | `positive_outlook` | 0.796 | no |
| `applications-problem-solving` | `complex_problem_solving` | 0.777 | no |
| `applications-self-driving_cars` | `transportation-autonomous_vehicles` | 0.755 | no |
| `future-transformation` | `sector_transformation` | 0.744 | no |
| `ease-work` | `impact-work_ease` | 0.743 | no |
| `negative_impacts-general` | `negative_impacts-human_subjugation` | 0.730 | no |
| `positive_impacts-stress_reduction` | `benefit-reduced_stress` | 0.729 | no |
| `key_sectors-health` | `AI-sector-focus-health` | 0.715 | no |
| `safety-home` | `safety-improvements-shelter_security` | 0.704 | no |
| `safety-cybersecurity` | `sector-focus-cyber_security` | 0.700 | no |
| `AI-autonomy` | `AI-automation_of_repetitive_tasks` | 0.698 | no |
| `applications-deep_fakes` | `concern-deepfakes` | 0.692 | no |
| `impact-jobs` | `AI-employment_transformation` | 0.679 | no |
| `negative_impacts-dependency` | `concern-human_dependency` | 0.670 | no |
| `negative_impacts-immobility` | `negative_impacts-laziness` | 0.658 | no |
| `positive_impacts-personalisation` | `personalisation-virtual_trials` | 0.658 | no |
| `AI-self-modification` | `AI-mindset_shift` | 0.654 | no |
| `impact-global` | `impact-technological_advancement` | 0.641 | no |
| `positive_impacts-automation` | `automation_of_repetitive_tasks` | 0.638 | no |
| `positive_impacts-problem-solving` | `daily_life_assistance-problem_resolution` | 0.623 | no |
| `negative_impacts-deskilling` | `impact-digital_exclusion` | 0.617 | no |
| `impact-misconception` | `impact-communication_enhancement` | 0.617 | no |
| `AI-speed` | `AI-omnipotence` | 0.617 | no |
| `applications-personal_assistant` | `AI-daily_life_assistance` | 0.605 | no |
| `applications-medical_care` | `accessibility-free_healthcare` | 0.605 | no |
| `applications-robotics` | `AI-role-human_replacement` | 0.598 | no |
| `improvement-future_readiness` | `ai-productivity_enhancement` | 0.596 | no |
| `positive_impacts-general` | `economic_impact-universal_basic_income` | 0.590 | no |
| `safety-privacy` | `ai-dependence-lifestyle` | 0.589 | no |
| `negative_impacts-danger_to_humans` | `AI-threat-to-humanity` | 0.588 | no |
| `improvement-accuracy` | `AI-productivity_enhancement` | 0.573 | no |
| `positive_impacts-jobs` | `labor-job_transformation` | 0.569 | no |
| `applications-voice_recognition` | `AI-ubiquity` | 0.566 | no |
| `ease-life` | `user_experience_relaxation` | 0.562 | no |
| `applications-chatbots` | `AI-role-expansion` | 0.559 | no |
| `future-hazard_avoidance` | `ai-utility` | 0.554 | no |
| `ease-travel` | `ubiquity` | 0.554 | no |
| `adoption-necessity` | `concern-ethical_development` | 0.552 | no |
| `improvement-quality_of_life` | `daily_life_assistance` | 0.550 | no |
| `positive_impacts-health` | `positive_outcomes-work_relief` | 0.547 | no |
| `negative_impacts-enslavement` | `concern-misuse` | 0.546 | no |
| `positive_impacts-cost_reduction` | `AI-economic_efficiency` | 0.527 | no |
| `jobs-computer_operator` | `labor-competitive_advantage` | 0.502 | no |
| `positive_impacts-upskilling` | `AI-positive_outlook` | 0.494 | no |
| `applications-text_generation` | `AI-multi-use` | 0.493 | no |
| `applications-simulation` | `complex_problem_solving-advance_analysis` | 0.480 | no |
| `progress-holistic` | `society-digital-transformation` | 0.464 | no |
| `applications-decision-making` | `AI-perception-central_role` | 0.432 | no |
| `jobs-nurse` | `AI-role_expansion` | 0.418 | no |

### Over-coding - machine codes with no human counterpart (49 codes, 145 segments)

| machine code | segments | responses | nearest human code | cosine |
|---|---:|---|---|---:|
| `AI-automation_of_repetitive_tasks` | 5 | 45, 51, 52, 81 | `AI-autonomy` | 0.698 |
| `AI-daily_life_assistance` | 4 | 52, 53, 84 | `AI-autonomy` | 0.641 |
| `AI-economic_efficiency` | 1 | 47 | `efficiency` | 0.725 |
| `AI-employment_transformation` | 4 | 45, 64, 81 | `impact-jobs` | 0.679 |
| `AI-mindset_shift` | 1 | 64 | `AI-self-modification` | 0.654 |
| `AI-multi-use` | 8 | 45, 51, 52, 53, 73, 81, 82 | `AI-autonomy` | 0.716 |
| `AI-omnipotence` | 3 | 67, 84 | `AI-autonomy` | 0.769 |
| `AI-perception-central_role` | 4 | 47, 52, 236 | `AI-superintelligence` | 0.558 |
| `AI-positive_outlook` | 5 | 43, 46, 73 | `future-positive` | 0.725 |
| `AI-productivity_enhancement` | 9 | 45, 46, 51, 53, 81, 90, 138 | `AI-autonomy` | 0.704 |
| `AI-role-expansion` | 1 | 67 | `AI-autonomy` | 0.662 |
| `AI-role-human_replacement` | 5 | 47, 51, 52, 80 | `AI-autonomy` | 0.661 |
| `AI-role_expansion` | 1 | 138 | `AI-autonomy` | 0.609 |
| `AI-sector-focus-health` | 2 | 88 | `key_sectors-health` | 0.715 |
| `AI-threat-to-humanity` | 1 | 100 | `AI-autonomy` | 0.618 |
| `AI-ubiquity` | 10 | 43, 51, 53, 64, 80, 82, 90, 138 | `AI-autonomy` | 0.746 |
| `accessibility-free_healthcare` | 1 | 88 | `applications-medical_care` | 0.605 |
| `ai-dependence-lifestyle` | 6 | 64, 80, 84, 236 | `AI-autonomy` | 0.681 |
| `ai-productivity_enhancement` | 1 | 90 | `AI-autonomy` | 0.693 |
| `ai-utility` | 4 | 81, 84, 138 | `AI-autonomy` | 0.762 |
| `automation_of_repetitive_tasks` | 1 | 53 | `positive_impacts-automation` | 0.638 |
| `benefit-reduced_stress` | 1 | 52 | `positive_impacts-stress_reduction` | 0.729 |
| `complex_problem_solving` | 2 | 82 | `applications-problem-solving` | 0.777 |
| `complex_problem_solving-advance_analysis` | 1 | 88 | `applications-problem-solving` | 0.679 |
| `concern-deepfakes` | 1 | 73 | `applications-deep_fakes` | 0.692 |
| `concern-ethical_development` | 3 | 67, 73 | `safety-privacy` | 0.566 |
| `concern-human_dependency` | 8 | 46, 67, 80, 100, 236 | `negative_impacts-dependency` | 0.670 |
| `concern-misuse` | 2 | 236 | `negative_impacts-misuse` | 0.698 |
| `daily_life_assistance` | 4 | 82, 90 | `ease-life` | 0.566 |
| `daily_life_assistance-problem_resolution` | 1 | 88 | `applications-problem-solving` | 0.640 |
| `economic_impact-universal_basic_income` | 1 | 47 | `impact-global` | 0.605 |
| `impact-communication_enhancement` | 1 | 53 | `impact-global` | 0.623 |
| `impact-digital_exclusion` | 1 | 100 | `impact-global` | 0.649 |
| `impact-technological_advancement` | 5 | 43, 64, 73, 82, 90 | `impact-global` | 0.641 |
| `impact-work_ease` | 4 | 43, 45, 81 | `ease-work` | 0.743 |
| `labor-competitive_advantage` | 1 | 64 | `efficiency` | 0.545 |
| `labor-job_transformation` | 3 | 47, 51, 138 | `future-transformation` | 0.688 |
| `negative_impacts-human_subjugation` | 1 | 100 | `negative_impacts-danger_to_humans` | 0.771 |
| `negative_impacts-laziness` | 3 | 46, 80 | `negative_impacts-deskilling` | 0.734 |
| `personalisation-virtual_trials` | 1 | 90 | `improvement-personalisation` | 0.660 |
| `positive_outcomes-work_relief` | 6 | 45, 46, 47, 81, 236 | `positive_impacts-stress_reduction` | 0.655 |
| `positive_outlook` | 10 | 52, 53, 64, 82, 84, 88, 90, 138, 236 | `future-positive` | 0.796 |
| `safety-improvements-shelter_security` | 1 | 52 | `safety-cybersecurity` | 0.720 |
| `sector-focus-cyber_security` | 1 | 81 | `safety-cybersecurity` | 0.700 |
| `sector_transformation` | 1 | 51 | `future-transformation` | 0.744 |
| `society-digital-transformation` | 1 | 80 | `future-transformation` | 0.656 |
| `transportation-autonomous_vehicles` | 2 | 51 | `applications-self-driving_cars` | 0.755 |
| `ubiquity` | 1 | 236 | `safety-privacy` | 0.585 |
| `user_experience_relaxation` | 1 | 81 | `ease-life` | 0.562 |

### Blind spots - human codes the machine never produced (64 codes, 154 segments)

The only place the negative example "you did not generate a new code" is observable:
a code never invented leaves no artefact inside a run. The segments themselves are in
the local run directory's `agreement.md`.

| human code | segments | responses | nearest machine code | cosine |
|---|---:|---|---|---:|
| `AI-autonomy` | 2 | 67, 100 | `AI-omnipotence` | 0.769 |
| `AI-self-modification` | 1 | 67 | `AI-mindset_shift` | 0.654 |
| `AI-speed` | 1 | 67 | `AI-economic_efficiency` | 0.632 |
| `adoption-high` | 5 | 51, 53, 82, 138, 236 | `concern-human_dependency` | 0.522 |
| `adoption-necessity` | 2 | 64 | `concern-human_dependency` | 0.605 |
| `adoption-present` | 4 | 43, 64, 138 | `personalisation` | 0.566 |
| `applications-chatbots` | 2 | 53, 81 | `ai-utility` | 0.601 |
| `applications-decision-making` | 1 | 82 | `complex_problem_solving` | 0.505 |
| `applications-deep_fakes` | 1 | 73 | `concern-deepfakes` | 0.692 |
| `applications-friend` | 5 | 43, 82, 84 | `personalisation` | 0.535 |
| `applications-information` | 1 | 138 | `ai-utility` | 0.516 |
| `applications-medical_care` | 1 | 52 | `accessibility-free_healthcare` | 0.605 |
| `applications-meetings` | 2 | 43, 45 | `ubiquity` | 0.416 |
| `applications-personal_assistant` | 2 | 81, 84 | `personalisation` | 0.612 |
| `applications-planning` | 1 | 45 | `personalisation` | 0.526 |
| `applications-problem-solving` | 2 | 84, 138 | `complex_problem_solving` | 0.777 |
| `applications-robotics` | 4 | 51, 52, 80 | `transportation-autonomous_vehicles` | 0.618 |
| `applications-search` | 4 | 45, 80, 81, 90 | `ai-utility` | 0.488 |
| `applications-self-driving_cars` | 1 | 51 | `transportation-autonomous_vehicles` | 0.755 |
| `applications-simulation` | 1 | 90 | `ai-utility` | 0.530 |
| `applications-summarising` | 2 | 81, 90 | `ai-utility` | 0.490 |
| `applications-text_generation` | 1 | 45 | `ai-utility` | 0.541 |
| `applications-voice_recognition` | 1 | 81 | `ai-utility` | 0.573 |
| `ease-life` | 8 | 43, 51, 53, 81, 84, 90 | `ai-utility` | 0.622 |
| `ease-travel` | 1 | 53 | `ai-utility` | 0.563 |
| `ease-work` | 7 | 43, 45, 46, 81 | `impact-work_ease` | 0.743 |
| `future-hazard_avoidance` | 2 | 67, 73 | `transportation-autonomous_vehicles` | 0.675 |
| `future-inevitability` | 5 | 43, 47, 51, 64, 138 | `ai-utility` | 0.531 |
| `future-negative` | 2 | 73, 100 | `negative_impacts-misuse` | 0.547 |
| `future-positive` | 7 | 45, 52, 53, 64, 84, 88 | `positive_outlook` | 0.796 |
| `future-transformation` | 5 | 51, 64, 81, 82, 90 | `sector_transformation` | 0.744 |
| `impact-global` | 2 | 47, 90 | `impact-digital_exclusion` | 0.649 |
| `impact-jobs` | 4 | 47, 51, 73 | `impact-work_ease` | 0.701 |
| `impact-misconception` | 1 | 82 | `negative_impacts-misuse` | 0.649 |
| `improvement-accuracy` | 3 | 51, 73, 84 | `AI-productivity_enhancement` | 0.573 |
| `improvement-future_readiness` | 1 | 88 | `ai-productivity_enhancement` | 0.596 |
| `improvement-quality_of_life` | 2 | 52, 88 | `safety-improvements-shelter_security` | 0.600 |
| `jobs-computer_operator` | 1 | 51 | `labor-job_transformation` | 0.566 |
| `jobs-nurse` | 1 | 52 | `labor-job_transformation` | 0.541 |
| `key_sectors-elder_care` | 2 | 52 | `AI-sector-focus-health` | 0.579 |
| `key_sectors-health` | 2 | 47, 88 | `AI-sector-focus-health` | 0.715 |
| `negative_impacts-danger_to_humans` | 2 | 67, 73 | `negative_impacts-human_subjugation` | 0.771 |
| `negative_impacts-dependency` | 4 | 46, 64, 80, 100 | `negative_impacts-misuse` | 0.753 |
| `negative_impacts-deskilling` | 3 | 46, 80 | `negative_impacts-misuse` | 0.840 |
| `negative_impacts-domination` | 1 | 80 | `negative_impacts-misuse` | 0.714 |
| `negative_impacts-enslavement` | 3 | 46, 67, 100 | `negative_impacts-misuse` | 0.790 |
| `negative_impacts-general` | 2 | 46, 73 | `negative_impacts-misuse` | 0.832 |
| `negative_impacts-immobility` | 1 | 80 | `negative_impacts-misuse` | 0.669 |
| `negative_impacts-lack_of_information` | 2 | 80, 100 | `negative_impacts-misuse` | 0.684 |
| `positive_impacts-automation` | 3 | 51, 53, 81 | `automation_of_repetitive_tasks` | 0.638 |
| `positive_impacts-cost_reduction` | 1 | 88 | `economic_impact-productivity_gain` | 0.645 |
| `positive_impacts-general` | 9 | 46, 64, 73, 88 | `economic_impact-productivity_gain` | 0.689 |
| `positive_impacts-health` | 1 | 88 | `economic_impact-productivity_gain` | 0.586 |
| `positive_impacts-jobs` | 1 | 64 | `economic_impact-productivity_gain` | 0.654 |
| `positive_impacts-personalisation` | 1 | 81 | `personalisation` | 0.732 |
| `positive_impacts-problem-solving` | 7 | 81, 82, 88, 90, 138 | `complex_problem_solving` | 0.642 |
| `positive_impacts-stress_reduction` | 1 | 52 | `benefit-reduced_stress` | 0.729 |
| `positive_impacts-upskilling` | 1 | 138 | `economic_impact-productivity_gain` | 0.606 |
| `progress-holistic` | 1 | 43 | `ai-productivity_enhancement` | 0.540 |
| `requirements-basic_income` | 1 | 47 | `economic_impact-universal_basic_income` | 0.534 |
| `requirements-regulation` | 3 | 46, 73 | `concern-misuse` | 0.495 |
| `safety-cybersecurity` | 1 | 81 | `safety-improvements-shelter_security` | 0.720 |
| `safety-home` | 1 | 52 | `safety-improvements-shelter_security` | 0.704 |
| `safety-privacy` | 1 | 81 | `safety-improvements-shelter_security` | 0.678 |
