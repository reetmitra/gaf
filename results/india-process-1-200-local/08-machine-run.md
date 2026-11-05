# 08 - The machine run (live-model coders), run id `local-cold200`

200 responses, 1524 segments, 1633 assignments, 162 codes in 48 families; embedding space `local-embeddinggemma-768`; offline: False.

**Caveats the run printed about itself:**


The two most-used machine codes account for 207 of 1633 assignments: `positive_outlook` 110, `AI-productivity_enhancement` 97. Read it as a property of these coders on this sample.

## Findings by check

| check | ERROR | WARN | INFO |
|---|---:|---:|---:|
| M1 | 0 | 835 | 302 |
| M2 | 0 | 696 | 725 |
| M3 | 6 | 29 | 1620 |
| S1 | 1 | 0 | 0 |
| S2 | 15 | 0 | 15 |
| S2b | 0 | 13 | 0 |
| S3 | 0 | 350 | 0 |
| S4 | 5 | 0 | 0 |
| S5 | 0 | 1 | 0 |
| S6 | 5 | 0 | 13 |

## Findings by marker

| check | severity | marker | n |
|---|---|---|---:|
| M1 | INFO | coders_agree | 302 |
| M1 | WARN | coder_unmatched | 214 |
| M1 | WARN | coders_dispute | 29 |
| M1 | WARN | grey_zone_judged | 592 |
| M2 | INFO | route_create | 9 |
| M2 | INFO | route_merge | 716 |
| M2 | WARN | route_judge | 696 |
| M3 | ERROR | candidate_dropped_no_evidence | 6 |
| M3 | INFO | fit_ok | 1620 |
| M3 | WARN | fit_imprecise | 1 |
| M3 | WARN | fit_incomplete | 22 |
| M3 | WARN | quote_removed_unnecessary | 6 |
| S1 | ERROR | missing_evidence | 1 |
| S2 | ERROR | no_verified_evidence | 15 |
| S2 | INFO | quote_unverified | 15 |
| S2b | WARN | quote_too_long | 11 |
| S2b | WARN | quote_too_long_words | 2 |
| S3 | WARN | sub_code_first | 350 |
| S4 | ERROR | too_many_codes_on_segment | 5 |
| S5 | WARN | too_few_codes | 1 |
| S6 | ERROR | duplicate_name | 5 |
| S6 | INFO | evidence_on_parent | 13 |

## Every ERROR and WARN (subject is the candidate or response concerned)

| check | severity | marker | subject | message | n |
|---|---|---|---|---|---:|
| M1 | WARN | coder_unmatched | (unmatched)<->AI-automation_of_repetitive_tasks | Coder B proposed 'AI-automation_of_repetitive_tasks' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-behavioral_influence | Coder B proposed 'AI-behavioral_influence' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-creative_capability | Coder B proposed 'AI-creative_capability' and the other coder proposed nothing that could be assigned to it. | 3 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-data-driven | Coder B proposed 'AI-data-driven' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-economic_efficiency | Coder B proposed 'AI-economic_efficiency' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-enhanced-communication | Coder B proposed 'AI-enhanced-communication' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-multi-use | Coder B proposed 'AI-multi-use' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-multi_use | Coder B proposed 'AI-multi_use' and the other coder proposed nothing that could be assigned to it. | 7 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-perception-central_role | Coder B proposed 'AI-perception-central_role' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-productivity_enhancement | Coder B proposed 'AI-productivity_enhancement' and the other coder proposed nothing that could be assigned to it. | 8 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-robotics_engineering | Coder B proposed 'AI-robotics_engineering' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-role_expansion | Coder B proposed 'AI-role_expansion' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-role_human_replacement | Coder B proposed 'AI-role_human_replacement' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-sector-focus-defence_education | Coder B proposed 'AI-sector-focus-defence_education' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-sector_transformation | Coder B proposed 'AI-sector_transformation' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-threat-to-humanity | Coder B proposed 'AI-threat-to-humanity' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-ubiquity | Coder B proposed 'AI-ubiquity' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-utility | Coder B proposed 'AI-utility' and the other coder proposed nothing that could be assigned to it. | 3 |
| M1 | WARN | coder_unmatched | (unmatched)<->accessibility-assistance_for_disabled | Coder B proposed 'accessibility-assistance_for_disabled' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->accessibility-free_healthcare | Coder B proposed 'accessibility-free_healthcare' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->ai-productivity_enhancement | Coder B proposed 'ai-productivity_enhancement' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->ai-role-human_replacement | Coder B proposed 'ai-role-human_replacement' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->ai-ubiquity | Coder B proposed 'ai-ubiquity' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->ai-unclear_outputs | Coder B proposed 'ai-unclear_outputs' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->ai-utility | Coder B proposed 'ai-utility' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->automation_of_repetitive_tasks | Coder B proposed 'automation_of_repetitive_tasks' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->benefit-reduced_stress | Coder B proposed 'benefit-reduced_stress' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->complex_problem_solving | Coder B proposed 'complex_problem_solving' and the other coder proposed nothing that could be assigned to it. | 3 |
| M1 | WARN | coder_unmatched | (unmatched)<->complex_problem_solving-advance_analysis | Coder B proposed 'complex_problem_solving-advance_analysis' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->complex_problem_solving-scientific_discovery | Coder B proposed 'complex_problem_solving-scientific_discovery' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->concern-deepfakes | Coder B proposed 'concern-deepfakes' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->concern-human_dependency | Coder B proposed 'concern-human_dependency' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->concern-privacy_security | Coder B proposed 'concern-privacy_security' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->creative_capability | Coder B proposed 'creative_capability' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->creative_capability-media_generation | Coder B proposed 'creative_capability-media_generation' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->daily_life_assistance | Coder B proposed 'daily_life_assistance' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->daily_life_assistance-automated_payments | Coder B proposed 'daily_life_assistance-automated_payments' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->daily_life_assistance-problem_resolution | Coder B proposed 'daily_life_assistance-problem_resolution' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->economic_impact-productivity_gain | Coder B proposed 'economic_impact-productivity_gain' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->education-literacy_requirement | Coder B proposed 'education-literacy_requirement' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->education-sector-transformation | Coder B proposed 'education-sector-transformation' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->education-sector_transformation | Coder B proposed 'education-sector_transformation' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->employment_transformation-job_displacement | Coder B proposed 'employment_transformation-job_displacement' and the other coder proposed nothing that could be assigned to it. | 3 |
| M1 | WARN | coder_unmatched | (unmatched)<->employment_transformation-job_transformation | Coder B proposed 'employment_transformation-job_transformation' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->global_defence | Coder B proposed 'global_defence' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->impact-communication_enhancement | Coder B proposed 'impact-communication_enhancement' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->impact-digital_exclusion | Coder B proposed 'impact-digital_exclusion' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->impact-enhanced-communication | Coder B proposed 'impact-enhanced-communication' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->impact-public_safety | Coder B proposed 'impact-public_safety' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->impact-technological_advancement | Coder B proposed 'impact-technological_advancement' and the other coder proposed nothing that could be assigned to it. | 17 |
| M1 | WARN | coder_unmatched | (unmatched)<->impact-work_ease | Coder B proposed 'impact-work_ease' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->labor-competitive_advantage | Coder B proposed 'labor-competitive_advantage' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->labor-job_transformation | Coder B proposed 'labor-job_transformation' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->need_for_awareness-literacy | Coder B proposed 'need_for_awareness-literacy' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->negative_impacts-dual_nature | Coder B proposed 'negative_impacts-dual_nature' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->negative_impacts-job_destruction | Coder B proposed 'negative_impacts-job_destruction' and the other coder proposed nothing that could be assigned to it. | 5 |
| M1 | WARN | coder_unmatched | (unmatched)<->negative_impacts-physical_health | Coder B proposed 'negative_impacts-physical_health' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->perception-central_role | Coder B proposed 'perception-central_role' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->positive_outcomes-work_relief | Coder B proposed 'positive_outcomes-work_relief' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->privacy_security-safe_sharing | Coder B proposed 'privacy_security-safe_sharing' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->resource-efficiency | Coder B proposed 'resource-efficiency' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->robotics_engineering | Coder B proposed 'robotics_engineering' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->role_human_replacement | Coder B proposed 'role_human_replacement' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->safety_improvements | Coder B proposed 'safety_improvements' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->sector-focus-education | Coder B proposed 'sector-focus-education' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->sector-focus-health | Coder B proposed 'sector-focus-health' and the other coder proposed nothing that could be assigned to it. | 3 |
| M1 | WARN | coder_unmatched | (unmatched)<->sector-focus-programming | Coder B proposed 'sector-focus-programming' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->sector-focus-transportation | Coder B proposed 'sector-focus-transportation' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->society-digital-transformation | Coder B proposed 'society-digital-transformation' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->society-social_norms | Coder B proposed 'society-social_norms' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->threat-to-humanity | Coder B proposed 'threat-to-humanity' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->transport_automation | Coder B proposed 'transport_automation' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->transportation-autonomous_vehicles | Coder B proposed 'transportation-autonomous_vehicles' and the other coder proposed nothing that could be assigned to it. | 4 |
| M1 | WARN | coder_unmatched | (unmatched)<->transportation-navigation_assistance | Coder B proposed 'transportation-navigation_assistance' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->ubiquity | Coder B proposed 'ubiquity' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->utility-efficiency_gain | Coder B proposed 'utility-efficiency_gain' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->utility-work_ease | Coder B proposed 'utility-work_ease' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->utility-work_efficiency | Coder B proposed 'utility-work_efficiency' and the other coder proposed nothing that could be assigned to it. | 4 |
| M1 | WARN | coder_unmatched | *message withheld: shares wording with a response* | *message withheld: shares wording with a response* | 3 |
| M1 | WARN | coder_unmatched | AI-assistance_for_disabled<->(unmatched) | Coder A proposed 'AI-assistance_for_disabled' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | AI-automation_of_repetitive_tasks<->(unmatched) | Coder A proposed 'AI-automation_of_repetitive_tasks' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | AI-education-sector-transformation<->(unmatched) | Coder A proposed 'AI-education-sector-transformation' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | AI-global_defence<->(unmatched) | Coder A proposed 'AI-global_defence' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | AI-impact-positive_outlook<->(unmatched) | Coder A proposed 'AI-impact-positive_outlook' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | AI-multi_use<->(unmatched) | Coder A proposed 'AI-multi_use' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | AI-perception-central_role<->(unmatched) | Coder A proposed 'AI-perception-central_role' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | AI-productivity_enhancement<->(unmatched) | Coder A proposed 'AI-productivity_enhancement' and the other coder proposed nothing that could be assigned to it. | 3 |
| M1 | WARN | coder_unmatched | AI-role-expansion<->(unmatched) | Coder A proposed 'AI-role-expansion' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | AI-role_human_replacement<->(unmatched) | Coder A proposed 'AI-role_human_replacement' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | AI-sector-focus-defence_education<->(unmatched) | Coder A proposed 'AI-sector-focus-defence_education' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | AI-ubiquity<->(unmatched) | Coder A proposed 'AI-ubiquity' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | AI-utility-work_ease<->(unmatched) | Coder A proposed 'AI-utility-work_ease' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | AI-utility<->(unmatched) | Coder A proposed 'AI-utility' and the other coder proposed nothing that could be assigned to it. | 3 |
| M1 | WARN | coder_unmatched | complex_problem_solving<->(unmatched) | Coder A proposed 'complex_problem_solving' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | concern-human_dependency<->(unmatched) | Coder A proposed 'concern-human_dependency' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | daily_life_assistance<->(unmatched) | Coder A proposed 'daily_life_assistance' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | economic_efficiency-productivity_gain<->(unmatched) | Coder A proposed 'economic_efficiency-productivity_gain' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | economic_efficiency<->(unmatched) | Coder A proposed 'economic_efficiency' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | economic_impact-productivity_gain<->(unmatched) | Coder A proposed 'economic_impact-productivity_gain' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | employment_transformation-job_displacement<->(unmatched) | Coder A proposed 'employment_transformation-job_displacement' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | employment_transformation<->(unmatched) | Coder A proposed 'employment_transformation' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | impact-digital_exclusion<->(unmatched) | Coder A proposed 'impact-digital_exclusion' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | mindset_shift<->(unmatched) | Coder A proposed 'mindset_shift' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | misuse<->(unmatched) | Coder A proposed 'misuse' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | multi-use<->(unmatched) | Coder A proposed 'multi-use' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | need_for_awareness<->(unmatched) | Coder A proposed 'need_for_awareness' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | negative_impacts-human_subjugation<->(unmatched) | Coder A proposed 'negative_impacts-human_subjugation' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | negative_impacts-misuse<->(unmatched) | Coder A proposed 'negative_impacts-misuse' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | perception-central_role<->(unmatched) | Coder A proposed 'perception-central_role' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | positive_outcomes-work_relief<->(unmatched) | Coder A proposed 'positive_outcomes-work_relief' and the other coder proposed nothing that could be assigned to it. | 3 |
| M1 | WARN | coder_unmatched | positive_outlook<->(unmatched) | Coder A proposed 'positive_outlook' and the other coder proposed nothing that could be assigned to it. | 10 |
| M1 | WARN | coder_unmatched | safety-reduced_accidents<->(unmatched) | Coder A proposed 'safety-reduced_accidents' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | sector-focus-digital_marketing<->(unmatched) | Coder A proposed 'sector-focus-digital_marketing' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | sector_transformation<->(unmatched) | Coder A proposed 'sector_transformation' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | society-digital-transformation<->(unmatched) | Coder A proposed 'society-digital-transformation' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | threat-to-humanity<->(unmatched) | Coder A proposed 'threat-to-humanity' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | transportation-autonomous_vehicles<->(unmatched) | Coder A proposed 'transportation-autonomous_vehicles' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | ubiquity<->(unmatched) | Coder A proposed 'ubiquity' and the other coder proposed nothing that could be assigned to it. | 4 |
| M1 | WARN | coder_unmatched | utility-work_ease<->(unmatched) | Coder A proposed 'utility-work_ease' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | utility<->(unmatched) | Coder A proposed 'utility' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coders_dispute | *message withheld: shares wording with a response* | *message withheld: shares wording with a response* | 1 |
| M1 | WARN | coders_dispute | AI-data-driven<->impact-technological_advancement | Coders dispute: 'AI-data-driven' and 'impact-technological_advancement' match at only cosine 0.447 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | AI-role-expansion<->education-literacy_requirement | Coders dispute: 'AI-role-expansion' and 'education-literacy_requirement' match at only cosine 0.399 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | AI-role-human_replacement<->impact-technological_advancement | Coders dispute: 'AI-role-human_replacement' and 'impact-technological_advancement' match at only cosine 0.426 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | AI-sector-focus-cyber_security<->security-cyber_security | Coders dispute: 'AI-sector-focus-cyber_security' and 'security-cyber_security' match at only cosine 0.423 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | AI-ubiquity<->AI-productivity_enhancement | Coders dispute: 'AI-ubiquity' and 'AI-productivity_enhancement' match at only cosine 0.419 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | AI-ubiquity<->negative_impacts-misuse | Coders dispute: 'AI-ubiquity' and 'negative_impacts-misuse' match at only cosine 0.417 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | AI-ubiquity<->positive_outlook | Coders dispute: 'AI-ubiquity' and 'positive_outlook' match at only cosine 0.432 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | AI-utility<->AI-robotics_engineering | Coders dispute: 'AI-utility' and 'AI-robotics_engineering' match at only cosine 0.427 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | AI-utility<->complex_problem_solving-scientific_discovery | Coders dispute: 'AI-utility' and 'complex_problem_solving-scientific_discovery' match at only cosine 0.378 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | ai-dependence-lifestyle<->AI-multi_use | Coders dispute: 'ai-dependence-lifestyle' and 'AI-multi_use' match at only cosine 0.418 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | ai-utility<->employment_transformation-job_creation | Coders dispute: 'ai-utility' and 'employment_transformation-job_creation' match at only cosine 0.415 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | ai-utility<->negative_impacts-laziness | Coders dispute: 'ai-utility' and 'negative_impacts-laziness' match at only cosine 0.416 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | concern-human_dependency<->negative_impacts-dual_nature | Coders dispute: 'concern-human_dependency' and 'negative_impacts-dual_nature' match at only cosine 0.430 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | daily_life_assistance-problem_resolution<->utility-work_ease | Coders dispute: 'daily_life_assistance-problem_resolution' and 'utility-work_ease' match at only cosine 0.393 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | economic_efficiency<->impact-work_ease | Coders dispute: 'economic_efficiency' and 'impact-work_ease' match at only cosine 0.425 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | employment_transformation-job_displacement<->utility-work_efficiency | Coders dispute: 'employment_transformation-job_displacement' and 'utility-work_efficiency' match at only cosine 0.235 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | employment_transformation<->impact-technological_advancement | Coders dispute: 'employment_transformation' and 'impact-technological_advancement' match at only cosine 0.379 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | negative_impacts<->perception-fleeting_trend | Coders dispute: 'negative_impacts' and 'perception-fleeting_trend' match at only cosine 0.405 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | perception-central_role<->AI-multi-use | Coders dispute: 'perception-central_role' and 'AI-multi-use' match at only cosine 0.414 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | positive_outlook<->AI-daily_life_assistance | Coders dispute: 'positive_outlook' and 'AI-daily_life_assistance' match at only cosine 0.418 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | positive_outlook<->AI-data_driven | Coders dispute: 'positive_outlook' and 'AI-data_driven' match at only cosine 0.380 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | positive_outlook<->AI-enhanced-communication | Coders dispute: 'positive_outlook' and 'AI-enhanced-communication' match at only cosine 0.432 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | positive_outlook<->negative_impacts-laziness | Coders dispute: 'positive_outlook' and 'negative_impacts-laziness' match at only cosine 0.280 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | positive_outlook<->safety-improvements-shelter_security | Coders dispute: 'positive_outlook' and 'safety-improvements-shelter_security' match at only cosine 0.214 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | positive_outlook<->transportation-autonomous_vehicles | Coders dispute: 'positive_outlook' and 'transportation-autonomous_vehicles' match at only cosine 0.352 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | threat-to-humanity<->need_for_awareness-literacy | Coders dispute: 'threat-to-humanity' and 'need_for_awareness-literacy' match at only cosine 0.434 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | ubiquity<->mindset_shift-problem_identification | Coders dispute: 'ubiquity' and 'mindset_shift-problem_identification' match at only cosine 0.355 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | ubiquity<->transportation-autonomous_vehicles | Coders dispute: 'ubiquity' and 'transportation-autonomous_vehicles' match at only cosine 0.359 (< tau_low 0.45). | 1 |
| M1 | WARN | grey_zone_judged | *message withheld: shares wording with a response* | *message withheld: shares wording with a response* | 13 |
| M1 | WARN | grey_zone_judged | AI-assistance_for_disabled<->AI-assistance_for_disabled | Grey zone ruled DROP: 'AI-assistance_for_disabled' and 'AI-assistance_for_disabled' match at cosine 0.707, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-assistance_for_disabled<->AI-assistance_for_disabled | Grey zone ruled DROP: 'AI-assistance_for_disabled' and 'AI-assistance_for_disabled' match at cosine 0.800, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-assistance_for_disabled<->accessibility-assistance_for_disabled | Grey zone ruled DROP: 'AI-assistance_for_disabled' and 'accessibility-assistance_for_disabled' match at cosine 0.723, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->AI-automation_of_repetitive_tasks | Grey zone ruled DROP: 'AI-automation_of_repetitive_tasks' and 'AI-automation_of_repetitive_tasks' match at cosine 0.642, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->AI-automation_of_repetitive_tasks | Grey zone ruled DROP: 'AI-automation_of_repetitive_tasks' and 'AI-automation_of_repetitive_tasks' match at cosine 0.686, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->AI-automation_of_repetitive_tasks | Grey zone ruled DROP: 'AI-automation_of_repetitive_tasks' and 'AI-automation_of_repetitive_tasks' match at cosine 0.694, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->AI-automation_of_repetitive_tasks | Grey zone ruled DROP: 'AI-automation_of_repetitive_tasks' and 'AI-automation_of_repetitive_tasks' match at cosine 0.724, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->AI-automation_of_repetitive_tasks | Grey zone ruled DROP: 'AI-automation_of_repetitive_tasks' and 'AI-automation_of_repetitive_tasks' match at cosine 0.746, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->AI-automation_of_repetitive_tasks | Grey zone ruled DROP: 'AI-automation_of_repetitive_tasks' and 'AI-automation_of_repetitive_tasks' match at cosine 0.762, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->AI-daily_life_assistance | Grey zone ruled KEEP: 'AI-automation_of_repetitive_tasks' and 'AI-daily_life_assistance' match at cosine 0.678, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->AI-productivity_enhancement | Grey zone ruled KEEP: 'AI-automation_of_repetitive_tasks' and 'AI-productivity_enhancement' match at cosine 0.539, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->ai-productivity_enhancement | Grey zone ruled DROP: 'AI-automation_of_repetitive_tasks' and 'ai-productivity_enhancement' match at cosine 0.657, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->daily_life_assistance-problem_resolution | Grey zone ruled DROP: 'AI-automation_of_repetitive_tasks' and 'daily_life_assistance-problem_resolution' match at cosine 0.655, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->labor-job_transformation | Grey zone ruled KEEP: 'AI-automation_of_repetitive_tasks' and 'labor-job_transformation' match at cosine 0.551, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->positive_outcomes-work_relief | Grey zone ruled DROP: 'AI-automation_of_repetitive_tasks' and 'positive_outcomes-work_relief' match at cosine 0.697, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->positive_outcomes-work_relief | Grey zone ruled KEEP: 'AI-automation_of_repetitive_tasks' and 'positive_outcomes-work_relief' match at cosine 0.727, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->utility-operational_automation | Grey zone ruled DROP: 'AI-automation_of_repetitive_tasks' and 'utility-operational_automation' match at cosine 0.784, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-behavioral_influence<->negative_impacts-laziness | Grey zone ruled DROP: 'AI-behavioral_influence' and 'negative_impacts-laziness' match at cosine 0.689, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-complex_problem_solving<->utility-problem_solving | Grey zone ruled DROP: 'AI-complex_problem_solving' and 'utility-problem_solving' match at cosine 0.741, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-creative_capability<->creative_capability-media_generation | Grey zone ruled DROP: 'AI-creative_capability' and 'creative_capability-media_generation' match at cosine 0.663, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-creative_capability<->creative_capability-media_generation | Grey zone ruled DROP: 'AI-creative_capability' and 'creative_capability-media_generation' match at cosine 0.759, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-creative_capability<->technology-media_manipulation | Grey zone ruled DROP: 'AI-creative_capability' and 'technology-media_manipulation' match at cosine 0.655, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-daily_life_assistance<->AI-daily_life_assistance | Grey zone ruled DROP: 'AI-daily_life_assistance' and 'AI-daily_life_assistance' match at cosine 0.697, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-daily_life_assistance<->ai-dependence-lifestyle | Grey zone ruled KEEP: 'AI-daily_life_assistance' and 'ai-dependence-lifestyle' match at cosine 0.590, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-daily_life_assistance<->utility-daily_assistance | Grey zone ruled DROP: 'AI-daily_life_assistance' and 'utility-daily_assistance' match at cosine 0.607, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-data-driven<->impact-technological_advancement | Grey zone ruled KEEP: 'AI-data-driven' and 'impact-technological_advancement' match at cosine 0.464, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-dependence-lifestyle<->AI-dependence-lifestyle | Grey zone ruled DROP: 'AI-dependence-lifestyle' and 'AI-dependence-lifestyle' match at cosine 0.778, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-dependence-lifestyle<->ai-dependence-lifestyle | Grey zone ruled KEEP: 'AI-dependence-lifestyle' and 'ai-dependence-lifestyle' match at cosine 0.738, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-dependence-lifestyle<->benefit-reduced_stress | Grey zone ruled DROP: 'AI-dependence-lifestyle' and 'benefit-reduced_stress' match at cosine 0.725, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-disaster_management<->impact-public_safety | Grey zone ruled KEEP: 'AI-disaster_management' and 'impact-public_safety' match at cosine 0.577, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-divine_connection<->culture-religious_integration | Grey zone ruled DROP: 'AI-divine_connection' and 'culture-religious_integration' match at cosine 0.565, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-economic_efficiency<->AI-economic_strengthening | Grey zone ruled DROP: 'AI-economic_efficiency' and 'AI-economic_strengthening' match at cosine 0.702, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-economic_efficiency<->AI-perception-central_role | Grey zone ruled KEEP: 'AI-economic_efficiency' and 'AI-perception-central_role' match at cosine 0.601, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-economic_efficiency<->economic_efficiency-productivity_gain | Grey zone ruled DROP: 'AI-economic_efficiency' and 'economic_efficiency-productivity_gain' match at cosine 0.739, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-economic_efficiency<->economic_impact-cost_reduction | Grey zone ruled DROP: 'AI-economic_efficiency' and 'economic_impact-cost_reduction' match at cosine 0.748, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-efficiency<->utility-time_reduction | Grey zone ruled DROP: 'AI-efficiency' and 'utility-time_reduction' match at cosine 0.681, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-employment_transformation<->AI-employment_transformation | Grey zone ruled DROP: 'AI-employment_transformation' and 'AI-employment_transformation' match at cosine 0.758, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-employment_transformation<->AI-multi_use | Grey zone ruled DROP: 'AI-employment_transformation' and 'AI-multi_use' match at cosine 0.771, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-employment_transformation<->AI-role_expansion | Grey zone ruled DROP: 'AI-employment_transformation' and 'AI-role_expansion' match at cosine 0.697, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-employment_transformation<->impact-technological_advancement | Grey zone ruled KEEP: 'AI-employment_transformation' and 'impact-technological_advancement' match at cosine 0.488, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-employment_transformation<->impact-work_ease | Grey zone ruled DROP: 'AI-employment_transformation' and 'impact-work_ease' match at cosine 0.660, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-employment_transformation<->labor-job_transformation | Grey zone ruled KEEP: 'AI-employment_transformation' and 'labor-job_transformation' match at cosine 0.649, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-enhanced-communication<->impact-digital_connectivity | Grey zone ruled KEEP: 'AI-enhanced-communication' and 'impact-digital_connectivity' match at cosine 0.512, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-entrepreneurial-support<->ai_utility-organizational_tools | Grey zone ruled DROP: 'AI-entrepreneurial-support' and 'ai_utility-organizational_tools' match at cosine 0.697, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-facilitated-collaboration<->impact-collaborative_work | Grey zone ruled DROP: 'AI-facilitated-collaboration' and 'impact-collaborative_work' match at cosine 0.556, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-global_defence<->AI-global_defence | Grey zone ruled DROP: 'AI-global_defence' and 'AI-global_defence' match at cosine 0.758, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-impact-immigration<->migration-easier_immigration | Grey zone ruled DROP: 'AI-impact-immigration' and 'migration-easier_immigration' match at cosine 0.572, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-impact-rapid_change<->impact-technological_advancement | Grey zone ruled DROP: 'AI-impact-rapid_change' and 'impact-technological_advancement' match at cosine 0.688, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-impact-women_safety<->impact-technological_advancement | Grey zone ruled KEEP: 'AI-impact-women_safety' and 'impact-technological_advancement' match at cosine 0.602, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-impact-women_safety<->safety-women_safety | Grey zone ruled DROP: 'AI-impact-women_safety' and 'safety-women_safety' match at cosine 0.723, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-impact-work_ease<->AI-role-human_replacement | Grey zone ruled KEEP: 'AI-impact-work_ease' and 'AI-role-human_replacement' match at cosine 0.716, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-mindset_shift<->attitude-mindset_shift | Grey zone ruled DROP: 'AI-mindset_shift' and 'attitude-mindset_shift' match at cosine 0.751, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-multi-use<->AI-daily_life_assistance | Grey zone ruled KEEP: 'AI-multi-use' and 'AI-daily_life_assistance' match at cosine 0.704, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-multi-use<->AI-employment_transformation | Grey zone ruled KEEP: 'AI-multi-use' and 'AI-employment_transformation' match at cosine 0.549, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-multi-use<->AI-multi-use | Grey zone ruled DROP: 'AI-multi-use' and 'AI-multi-use' match at cosine 0.758, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-multi-use<->AI-productivity_enhancement | Grey zone ruled KEEP: 'AI-multi-use' and 'AI-productivity_enhancement' match at cosine 0.766, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-multi_use<->AI-multi_use | Grey zone ruled DROP: 'AI-multi_use' and 'AI-multi_use' match at cosine 0.679, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-multi_use<->education-sector_transformation | Grey zone ruled KEEP: 'AI-multi_use' and 'education-sector_transformation' match at cosine 0.585, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-need_for_awareness<->concern-human_dependency | Grey zone ruled DROP: 'AI-need_for_awareness' and 'concern-human_dependency' match at cosine 0.579, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-need_for_awareness<->employment_transformation-workforce_retraining | Grey zone ruled DROP: 'AI-need_for_awareness' and 'employment_transformation-workforce_retraining' match at cosine 0.685, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-need_for_awareness<->need_for_awareness-public_education | Grey zone ruled DROP: 'AI-need_for_awareness' and 'need_for_awareness-public_education' match at cosine 0.782, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-omnipotence<->AI-multi-use | Grey zone ruled DROP: 'AI-omnipotence' and 'AI-multi-use' match at cosine 0.604, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-omnipotence<->AI-omnipotence | Grey zone ruled DROP: 'AI-omnipotence' and 'AI-omnipotence' match at cosine 0.721, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-omnipotence<->ai-reliability | Grey zone ruled DROP: 'AI-omnipotence' and 'ai-reliability' match at cosine 0.607, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-perception-central_role<->AI-perception-central_role | Grey zone ruled DROP: 'AI-perception-central_role' and 'AI-perception-central_role' match at cosine 0.753, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-positive_outlook<->AI-positive_outlook | Grey zone ruled DROP: 'AI-positive_outlook' and 'AI-positive_outlook' match at cosine 0.786, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-positive_outlook<->AI-positive_outlook | Grey zone ruled DROP: 'AI-positive_outlook' and 'AI-positive_outlook' match at cosine 0.796, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-positive_outlook<->AI-positive_outlook | Grey zone ruled KEEP: 'AI-positive_outlook' and 'AI-positive_outlook' match at cosine 0.747, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-positive_outlook<->AI-productivity_enhancement | Grey zone ruled KEEP: 'AI-positive_outlook' and 'AI-productivity_enhancement' match at cosine 0.529, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-positive_outlook<->AI-utility | Grey zone ruled KEEP: 'AI-positive_outlook' and 'AI-utility' match at cosine 0.502, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-positive_outlook<->impact-positive_outcomes | Grey zone ruled DROP: 'AI-positive_outlook' and 'impact-positive_outcomes' match at cosine 0.625, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-positive_outlook<->impact-technological_advancement | Grey zone ruled KEEP: 'AI-positive_outlook' and 'impact-technological_advancement' match at cosine 0.588, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-positive_outlook<->negative_impacts-misuse | Grey zone ruled KEEP: 'AI-positive_outlook' and 'negative_impacts-misuse' match at cosine 0.552, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-positive_outlook<->utility-work_efficiency | Grey zone ruled KEEP: 'AI-positive_outlook' and 'utility-work_efficiency' match at cosine 0.465, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-automation_of_repetitive_tasks | Grey zone ruled KEEP: 'AI-productivity_enhancement' and 'AI-automation_of_repetitive_tasks' match at cosine 0.508, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-data-driven | Grey zone ruled KEEP: 'AI-productivity_enhancement' and 'AI-data-driven' match at cosine 0.591, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.573, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.587, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.598, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.629, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.639, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.659, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.664, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.690, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.694, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.717, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.733, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.744, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.756, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.758, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.761, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.762, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.774, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->ai-utility | Grey zone ruled KEEP: 'AI-productivity_enhancement' and 'ai-utility' match at cosine 0.556, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->benefit-reduced_stress | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'benefit-reduced_stress' match at cosine 0.633, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->daily_life_assistance-problem_resolution | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'daily_life_assistance-problem_resolution' match at cosine 0.720, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->impact-technological_advancement | Grey zone ruled KEEP: 'AI-productivity_enhancement' and 'impact-technological_advancement' match at cosine 0.569, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->utility-efficiency_gains | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'utility-efficiency_gains' match at cosine 0.702, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->utility-work_efficiency | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'utility-work_efficiency' match at cosine 0.666, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->utility-work_efficiency | Grey zone ruled KEEP: 'AI-productivity_enhancement' and 'utility-work_efficiency' match at cosine 0.555, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-robotics_engineering<->sector-focus-hospitality | Grey zone ruled KEEP: 'AI-robotics_engineering' and 'sector-focus-hospitality' match at cosine 0.595, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-expansion<->AI-role-expansion | Grey zone ruled KEEP: 'AI-role-expansion' and 'AI-role-expansion' match at cosine 0.782, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-expansion<->AI-role_human_replacement | Grey zone ruled DROP: 'AI-role-expansion' and 'AI-role_human_replacement' match at cosine 0.715, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-expansion<->AI-superintelligence | Grey zone ruled KEEP: 'AI-role-expansion' and 'AI-superintelligence' match at cosine 0.598, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-expansion<->ai-versatility | Grey zone ruled DROP: 'AI-role-expansion' and 'ai-versatility' match at cosine 0.660, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->AI-productivity_enhancement | Grey zone ruled KEEP: 'AI-role-human_replacement' and 'AI-productivity_enhancement' match at cosine 0.638, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->AI-role-human_replacement | Grey zone ruled DROP: 'AI-role-human_replacement' and 'AI-role-human_replacement' match at cosine 0.657, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->AI-role-human_replacement | Grey zone ruled DROP: 'AI-role-human_replacement' and 'AI-role-human_replacement' match at cosine 0.717, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->AI-role-human_replacement | Grey zone ruled DROP: 'AI-role-human_replacement' and 'AI-role-human_replacement' match at cosine 0.718, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->AI-role-human_replacement | Grey zone ruled DROP: 'AI-role-human_replacement' and 'AI-role-human_replacement' match at cosine 0.738, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->AI-role-human_replacement | Grey zone ruled DROP: 'AI-role-human_replacement' and 'AI-role-human_replacement' match at cosine 0.799, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->AI-role_human_replacement | Grey zone ruled DROP: 'AI-role-human_replacement' and 'AI-role_human_replacement' match at cosine 0.675, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->AI-role_human_replacement | Grey zone ruled KEEP: 'AI-role-human_replacement' and 'AI-role_human_replacement' match at cosine 0.761, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->employment_transformation-remote_work | Grey zone ruled KEEP: 'AI-role-human_replacement' and 'employment_transformation-remote_work' match at cosine 0.564, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->impact-public_safety | Grey zone ruled KEEP: 'AI-role-human_replacement' and 'impact-public_safety' match at cosine 0.531, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->impact-work_ease | Grey zone ruled KEEP: 'AI-role-human_replacement' and 'impact-work_ease' match at cosine 0.585, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->impact-work_ease | Grey zone ruled KEEP: 'AI-role-human_replacement' and 'impact-work_ease' match at cosine 0.597, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->labor-automation_of_work | Grey zone ruled DROP: 'AI-role-human_replacement' and 'labor-automation_of_work' match at cosine 0.691, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->safety-human_safety | Grey zone ruled KEEP: 'AI-role-human_replacement' and 'safety-human_safety' match at cosine 0.466, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->transportation-autonomous_vehicles | Grey zone ruled KEEP: 'AI-role-human_replacement' and 'transportation-autonomous_vehicles' match at cosine 0.696, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector-focus-defence_education<->sector_impact-defense_and_education | Grey zone ruled DROP: 'AI-sector-focus-defence_education' and 'sector_impact-defense_and_education' match at cosine 0.709, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector-focus-digital_marketing<->marketing-digital_marketing | Grey zone ruled DROP: 'AI-sector-focus-digital_marketing' and 'marketing-digital_marketing' match at cosine 0.604, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector-focus-education<->education-sector-transformation | Grey zone ruled DROP: 'AI-sector-focus-education' and 'education-sector-transformation' match at cosine 0.799, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector-focus-health<->AI-multi_use | Grey zone ruled KEEP: 'AI-sector-focus-health' and 'AI-multi_use' match at cosine 0.513, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector-focus-health<->AI-sector-focus-health | Grey zone ruled DROP: 'AI-sector-focus-health' and 'AI-sector-focus-health' match at cosine 0.702, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector-focus-health<->AI-sector-focus-health | Grey zone ruled DROP: 'AI-sector-focus-health' and 'AI-sector-focus-health' match at cosine 0.756, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector-focus-health<->AI-sector-focus-health | Grey zone ruled DROP: 'AI-sector-focus-health' and 'AI-sector-focus-health' match at cosine 0.764, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector-focus-health<->AI-sector-focus-health | Grey zone ruled DROP: 'AI-sector-focus-health' and 'AI-sector-focus-health' match at cosine 0.776, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector-focus-health<->AI-sector_focus-health | Grey zone ruled DROP: 'AI-sector-focus-health' and 'AI-sector_focus-health' match at cosine 0.693, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector-focus-transportation<->impact-public_safety | Grey zone ruled KEEP: 'AI-sector-focus-transportation' and 'impact-public_safety' match at cosine 0.518, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector-focus-transportation<->transportation-autonomous_vehicles | Grey zone ruled DROP: 'AI-sector-focus-transportation' and 'transportation-autonomous_vehicles' match at cosine 0.671, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector_transformation<->AI-sector_transformation | Grey zone ruled DROP: 'AI-sector_transformation' and 'AI-sector_transformation' match at cosine 0.732, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector_transformation<->AI-sector_transformation | Grey zone ruled DROP: 'AI-sector_transformation' and 'AI-sector_transformation' match at cosine 0.743, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector_transformation<->AI-sector_transformation | Grey zone ruled DROP: 'AI-sector_transformation' and 'AI-sector_transformation' match at cosine 0.761, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector_transformation<->impact-infrastructure_improvement | Grey zone ruled DROP: 'AI-sector_transformation' and 'impact-infrastructure_improvement' match at cosine 0.687, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-superintelligence<->AI-superintelligence | Grey zone ruled DROP: 'AI-superintelligence' and 'AI-superintelligence' match at cosine 0.742, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-superintelligence<->impact-technological_advancement | Grey zone ruled KEEP: 'AI-superintelligence' and 'impact-technological_advancement' match at cosine 0.547, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-transportation-autonomous_vehicles<->sector-focus-transportation | Grey zone ruled KEEP: 'AI-transportation-autonomous_vehicles' and 'sector-focus-transportation' match at cosine 0.541, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-ubiquity<->AI-daily_life_assistance | Grey zone ruled KEEP: 'AI-ubiquity' and 'AI-daily_life_assistance' match at cosine 0.590, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-ubiquity<->AI-ubiquity | Grey zone ruled DROP: 'AI-ubiquity' and 'AI-ubiquity' match at cosine 0.749, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-ubiquity<->AI-utility | Grey zone ruled KEEP: 'AI-ubiquity' and 'AI-utility' match at cosine 0.677, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-ubiquity<->accessibility-affordable_access | Grey zone ruled DROP: 'AI-ubiquity' and 'accessibility-affordable_access' match at cosine 0.697, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-ubiquity<->ai-multi-use | Grey zone ruled DROP: 'AI-ubiquity' and 'ai-multi-use' match at cosine 0.594, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-ubiquity<->impact-technological_advancement | Grey zone ruled DROP: 'AI-ubiquity' and 'impact-technological_advancement' match at cosine 0.588, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-ubiquity<->impact-work_ease | Grey zone ruled KEEP: 'AI-ubiquity' and 'impact-work_ease' match at cosine 0.522, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-ubiquity<->perception-technological_luck | Grey zone ruled KEEP: 'AI-ubiquity' and 'perception-technological_luck' match at cosine 0.493, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-ubiquity<->sector-focus-digital_marketing | Grey zone ruled KEEP: 'AI-ubiquity' and 'sector-focus-digital_marketing' match at cosine 0.535, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->AI-complex_problem_solving | Grey zone ruled KEEP: 'AI-utility' and 'AI-complex_problem_solving' match at cosine 0.609, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->AI-multi-use | Grey zone ruled DROP: 'AI-utility' and 'AI-multi-use' match at cosine 0.689, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->AI-multi-use | Grey zone ruled KEEP: 'AI-utility' and 'AI-multi-use' match at cosine 0.652, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->AI-multi_use | Grey zone ruled DROP: 'AI-utility' and 'AI-multi_use' match at cosine 0.719, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->AI-omnipotence | Grey zone ruled KEEP: 'AI-utility' and 'AI-omnipotence' match at cosine 0.587, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->AI-productivity_enhancement | Grey zone ruled KEEP: 'AI-utility' and 'AI-productivity_enhancement' match at cosine 0.712, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->AI-role_expansion | Grey zone ruled KEEP: 'AI-utility' and 'AI-role_expansion' match at cosine 0.569, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->AI-utility | Grey zone ruled DROP: 'AI-utility' and 'AI-utility' match at cosine 0.766, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->AI-utility | Grey zone ruled KEEP: 'AI-utility' and 'AI-utility' match at cosine 0.702, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->AI-utility | Grey zone ruled KEEP: 'AI-utility' and 'AI-utility' match at cosine 0.734, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->AI-utility | Grey zone ruled KEEP: 'AI-utility' and 'AI-utility' match at cosine 0.769, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->AI-utility | Grey zone ruled KEEP: 'AI-utility' and 'AI-utility' match at cosine 0.792, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->ai-daily_life_assistance | Grey zone ruled DROP: 'AI-utility' and 'ai-daily_life_assistance' match at cosine 0.573, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->ai-multi_use | Grey zone ruled KEEP: 'AI-utility' and 'ai-multi_use' match at cosine 0.692, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->ai-utility | Grey zone ruled DROP: 'AI-utility' and 'ai-utility' match at cosine 0.727, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->creative_capability | Grey zone ruled KEEP: 'AI-utility' and 'creative_capability' match at cosine 0.746, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->daily_life_assistance-automated_payments | Grey zone ruled DROP: 'AI-utility' and 'daily_life_assistance-automated_payments' match at cosine 0.623, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->impact-digital_connectivity | Grey zone ruled KEEP: 'AI-utility' and 'impact-digital_connectivity' match at cosine 0.615, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->negative_impacts-dual_nature | Grey zone ruled KEEP: 'AI-utility' and 'negative_impacts-dual_nature' match at cosine 0.560, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->sector-focus-education | Grey zone ruled DROP: 'AI-utility' and 'sector-focus-education' match at cosine 0.756, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | accessibility-assistance_for_disabled<->accessibility-inclusive_mobility | Grey zone ruled DROP: 'accessibility-assistance_for_disabled' and 'accessibility-inclusive_mobility' match at cosine 0.754, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-dependence-lifestyle<->AI-daily_life_assistance | Grey zone ruled DROP: 'ai-dependence-lifestyle' and 'AI-daily_life_assistance' match at cosine 0.770, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-dependence-lifestyle<->AI-dependence-lifestyle | Grey zone ruled DROP: 'ai-dependence-lifestyle' and 'AI-dependence-lifestyle' match at cosine 0.747, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-dependence-lifestyle<->AI-dependence-lifestyle | Grey zone ruled KEEP: 'ai-dependence-lifestyle' and 'AI-dependence-lifestyle' match at cosine 0.735, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-dependence-lifestyle<->AI-role_human_replacement | Grey zone ruled DROP: 'ai-dependence-lifestyle' and 'AI-role_human_replacement' match at cosine 0.670, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-dependence-lifestyle<->ai-dependence-lifestyle | Grey zone ruled DROP: 'ai-dependence-lifestyle' and 'ai-dependence-lifestyle' match at cosine 0.681, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-dependence-lifestyle<->ai-dependence-lifestyle | Grey zone ruled DROP: 'ai-dependence-lifestyle' and 'ai-dependence-lifestyle' match at cosine 0.740, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-dependence-lifestyle<->ai-dependence-lifestyle | Grey zone ruled DROP: 'ai-dependence-lifestyle' and 'ai-dependence-lifestyle' match at cosine 0.770, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-dependence-lifestyle<->concern-human_dependency | Grey zone ruled DROP: 'ai-dependence-lifestyle' and 'concern-human_dependency' match at cosine 0.722, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-dependence-lifestyle<->daily_life_assistance | Grey zone ruled KEEP: 'ai-dependence-lifestyle' and 'daily_life_assistance' match at cosine 0.457, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-dependence-lifestyle<->impact-technological_advancement | Grey zone ruled KEEP: 'ai-dependence-lifestyle' and 'impact-technological_advancement' match at cosine 0.627, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-dependence-lifestyle<->impact-technological_advancement | Grey zone ruled KEEP: 'ai-dependence-lifestyle' and 'impact-technological_advancement' match at cosine 0.681, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-dependence-lifestyle<->impact-work_ease | Grey zone ruled KEEP: 'ai-dependence-lifestyle' and 'impact-work_ease' match at cosine 0.644, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-dependence-lifestyle<->negative_impacts-laziness | Grey zone ruled DROP: 'ai-dependence-lifestyle' and 'negative_impacts-laziness' match at cosine 0.688, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-positive_outlook<->AI-perception-central_role | Grey zone ruled KEEP: 'ai-positive_outlook' and 'AI-perception-central_role' match at cosine 0.462, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-sector-focus-health<->AI-sector-focus-health | Grey zone ruled DROP: 'ai-sector-focus-health' and 'AI-sector-focus-health' match at cosine 0.762, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-unclear_outputs<->ai-unclear_outputs | Grey zone ruled KEEP: 'ai-unclear_outputs' and 'ai-unclear_outputs' match at cosine 0.787, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-utility<->AI-daily_life_assistance | Grey zone ruled KEEP: 'ai-utility' and 'AI-daily_life_assistance' match at cosine 0.630, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-utility<->AI-productivity_enhancement | Grey zone ruled DROP: 'ai-utility' and 'AI-productivity_enhancement' match at cosine 0.657, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-utility<->AI-productivity_enhancement | Grey zone ruled KEEP: 'ai-utility' and 'AI-productivity_enhancement' match at cosine 0.501, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-utility<->AI-productivity_enhancement | Grey zone ruled KEEP: 'ai-utility' and 'AI-productivity_enhancement' match at cosine 0.578, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-utility<->AI-role_human_replacement | Grey zone ruled KEEP: 'ai-utility' and 'AI-role_human_replacement' match at cosine 0.683, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-utility<->ai-utility | Grey zone ruled DROP: 'ai-utility' and 'ai-utility' match at cosine 0.794, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | automation_of_repetitive_tasks<->AI-automation_of_repetitive_tasks | Grey zone ruled DROP: 'automation_of_repetitive_tasks' and 'AI-automation_of_repetitive_tasks' match at cosine 0.702, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | automation_of_repetitive_tasks<->automation_of_repetitive_tasks | Grey zone ruled DROP: 'automation_of_repetitive_tasks' and 'automation_of_repetitive_tasks' match at cosine 0.675, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | benefit-reduced_stress<->benefit-reduced_stress | Grey zone ruled DROP: 'benefit-reduced_stress' and 'benefit-reduced_stress' match at cosine 0.684, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | complex_problem_solving-advance_analysis<->AI-productivity_enhancement | Grey zone ruled DROP: 'complex_problem_solving-advance_analysis' and 'AI-productivity_enhancement' match at cosine 0.600, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | complex_problem_solving<->AI-data-driven | Grey zone ruled KEEP: 'complex_problem_solving' and 'AI-data-driven' match at cosine 0.602, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | complex_problem_solving<->complex_problem_solving | Grey zone ruled DROP: 'complex_problem_solving' and 'complex_problem_solving' match at cosine 0.800, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | complex_problem_solving<->complex_problem_solving | Grey zone ruled KEEP: 'complex_problem_solving' and 'complex_problem_solving' match at cosine 0.710, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | complex_problem_solving<->complex_problem_solving | Grey zone ruled KEEP: 'complex_problem_solving' and 'complex_problem_solving' match at cosine 0.791, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | complex_problem_solving<->complex_problem_solving-advance_analysis | Grey zone ruled DROP: 'complex_problem_solving' and 'complex_problem_solving-advance_analysis' match at cosine 0.771, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | complex_problem_solving<->complex_problem_solving-advance_analysis | Grey zone ruled KEEP: 'complex_problem_solving' and 'complex_problem_solving-advance_analysis' match at cosine 0.643, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | complex_problem_solving<->positive_outcomes-accessible_healthcare | Grey zone ruled KEEP: 'complex_problem_solving' and 'positive_outcomes-accessible_healthcare' match at cosine 0.581, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | complex_problem_solving<->positive_outcomes-work_relief | Grey zone ruled KEEP: 'complex_problem_solving' and 'positive_outcomes-work_relief' match at cosine 0.488, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-ethical_development<->concern-ethical_development | Grey zone ruled DROP: 'concern-ethical_development' and 'concern-ethical_development' match at cosine 0.730, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-ethical_development<->concern-ethical_development | Grey zone ruled DROP: 'concern-ethical_development' and 'concern-ethical_development' match at cosine 0.766, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-ethical_development<->concern-regulatory_oversight | Grey zone ruled DROP: 'concern-ethical_development' and 'concern-regulatory_oversight' match at cosine 0.662, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-human_dependency<->AI-global_defence | Grey zone ruled KEEP: 'concern-human_dependency' and 'AI-global_defence' match at cosine 0.552, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-human_dependency<->impact-work_ease | Grey zone ruled KEEP: 'concern-human_dependency' and 'impact-work_ease' match at cosine 0.516, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-human_dependency<->need_for_awareness | Grey zone ruled DROP: 'concern-human_dependency' and 'need_for_awareness' match at cosine 0.611, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-human_dependency<->negative_impacts-misuse | Grey zone ruled KEEP: 'concern-human_dependency' and 'negative_impacts-misuse' match at cosine 0.651, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-privacy_security<->concern-data_privacy | Grey zone ruled DROP: 'concern-privacy_security' and 'concern-data_privacy' match at cosine 0.698, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-privacy_security<->concern-privacy_security | Grey zone ruled DROP: 'concern-privacy_security' and 'concern-privacy_security' match at cosine 0.662, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-privacy_security<->concern-privacy_security | Grey zone ruled DROP: 'concern-privacy_security' and 'concern-privacy_security' match at cosine 0.691, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-privacy_security<->concern-privacy_security | Grey zone ruled DROP: 'concern-privacy_security' and 'concern-privacy_security' match at cosine 0.768, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-privacy_security<->concern-privacy_security | Grey zone ruled DROP: 'concern-privacy_security' and 'concern-privacy_security' match at cosine 0.769, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-privacy_security<->concern-privacy_security | Grey zone ruled DROP: 'concern-privacy_security' and 'concern-privacy_security' match at cosine 0.780, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-privacy_security<->privacy_security-safe_sharing | Grey zone ruled KEEP: 'concern-privacy_security' and 'privacy_security-safe_sharing' match at cosine 0.631, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | creative_capability<->AI-creative_capability | Grey zone ruled DROP: 'creative_capability' and 'AI-creative_capability' match at cosine 0.693, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance-automated_reminders<->AI-daily_life_assistance | Grey zone ruled DROP: 'daily_life_assistance-automated_reminders' and 'AI-daily_life_assistance' match at cosine 0.749, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance-problem_resolution<->AI-daily_life_assistance | Grey zone ruled DROP: 'daily_life_assistance-problem_resolution' and 'AI-daily_life_assistance' match at cosine 0.611, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance-problem_resolution<->AI-daily_life_assistance | Grey zone ruled KEEP: 'daily_life_assistance-problem_resolution' and 'AI-daily_life_assistance' match at cosine 0.648, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance-problem_resolution<->AI-positive_outlook | Grey zone ruled KEEP: 'daily_life_assistance-problem_resolution' and 'AI-positive_outlook' match at cosine 0.654, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance-problem_resolution<->AI-utility | Grey zone ruled KEEP: 'daily_life_assistance-problem_resolution' and 'AI-utility' match at cosine 0.545, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance-problem_resolution<->daily_life_assistance-problem_resolution | Grey zone ruled DROP: 'daily_life_assistance-problem_resolution' and 'daily_life_assistance-problem_resolution' match at cosine 0.765, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->AI-daily_life_assistance | Grey zone ruled DROP: 'daily_life_assistance' and 'AI-daily_life_assistance' match at cosine 0.789, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->AI-daily_life_assistance | Grey zone ruled KEEP: 'daily_life_assistance' and 'AI-daily_life_assistance' match at cosine 0.752, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->AI-productivity_enhancement | Grey zone ruled KEEP: 'daily_life_assistance' and 'AI-productivity_enhancement' match at cosine 0.597, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->AI-productivity_enhancement | Grey zone ruled KEEP: 'daily_life_assistance' and 'AI-productivity_enhancement' match at cosine 0.612, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->AI-role_human_replacement | Grey zone ruled KEEP: 'daily_life_assistance' and 'AI-role_human_replacement' match at cosine 0.676, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->ai-utility | Grey zone ruled DROP: 'daily_life_assistance' and 'ai-utility' match at cosine 0.666, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->complex_problem_solving-advance_analysis | Grey zone ruled KEEP: 'daily_life_assistance' and 'complex_problem_solving-advance_analysis' match at cosine 0.621, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->creative_capability | Grey zone ruled KEEP: 'daily_life_assistance' and 'creative_capability' match at cosine 0.484, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->daily_life_assistance | Grey zone ruled DROP: 'daily_life_assistance' and 'daily_life_assistance' match at cosine 0.724, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->daily_life_assistance | Grey zone ruled DROP: 'daily_life_assistance' and 'daily_life_assistance' match at cosine 0.749, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->daily_life_assistance | Grey zone ruled KEEP: 'daily_life_assistance' and 'daily_life_assistance' match at cosine 0.619, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->daily_life_assistance-personal_assistants | Grey zone ruled DROP: 'daily_life_assistance' and 'daily_life_assistance-personal_assistants' match at cosine 0.754, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->daily_life_assistance-problem_resolution | Grey zone ruled DROP: 'daily_life_assistance' and 'daily_life_assistance-problem_resolution' match at cosine 0.679, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->daily_life_assistance-problem_resolution | Grey zone ruled KEEP: 'daily_life_assistance' and 'daily_life_assistance-problem_resolution' match at cosine 0.734, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->impact-communication_enhancement | Grey zone ruled KEEP: 'daily_life_assistance' and 'impact-communication_enhancement' match at cosine 0.645, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->impact-work_ease | Grey zone ruled KEEP: 'daily_life_assistance' and 'impact-work_ease' match at cosine 0.644, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->positive_outcomes-work_relief | Grey zone ruled KEEP: 'daily_life_assistance' and 'positive_outcomes-work_relief' match at cosine 0.723, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->utility-work_ease | Grey zone ruled DROP: 'daily_life_assistance' and 'utility-work_ease' match at cosine 0.631, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | data-driven<->AI-data-driven | Grey zone ruled KEEP: 'data-driven' and 'AI-data-driven' match at cosine 0.713, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | deepfakes<->concern-deepfakes | Grey zone ruled DROP: 'deepfakes' and 'concern-deepfakes' match at cosine 0.725, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | deepfakes<->concern-deepfakes | Grey zone ruled KEEP: 'deepfakes' and 'concern-deepfakes' match at cosine 0.601, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | dependence-lifestyle<->benefit-reduced_stress | Grey zone ruled KEEP: 'dependence-lifestyle' and 'benefit-reduced_stress' match at cosine 0.641, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency-productivity_gain<->AI-economic_strengthening | Grey zone ruled DROP: 'economic_efficiency-productivity_gain' and 'AI-economic_strengthening' match at cosine 0.645, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency-productivity_gain<->AI-employment_transformation | Grey zone ruled KEEP: 'economic_efficiency-productivity_gain' and 'AI-employment_transformation' match at cosine 0.549, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency-productivity_gain<->AI-productivity_enhancement | Grey zone ruled DROP: 'economic_efficiency-productivity_gain' and 'AI-productivity_enhancement' match at cosine 0.691, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency-productivity_gain<->impact-technological_advancement | Grey zone ruled KEEP: 'economic_efficiency-productivity_gain' and 'impact-technological_advancement' match at cosine 0.553, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency-productivity_gain<->sector-focus-programming | Grey zone ruled KEEP: 'economic_efficiency-productivity_gain' and 'sector-focus-programming' match at cosine 0.679, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency-productivity_gain<->utility-work_efficiency | Grey zone ruled DROP: 'economic_efficiency-productivity_gain' and 'utility-work_efficiency' match at cosine 0.637, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency-recession<->economic_efficiency-productivity_gain | Grey zone ruled KEEP: 'economic_efficiency-recession' and 'economic_efficiency-productivity_gain' match at cosine 0.614, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency<->AI-creative_capability | Grey zone ruled KEEP: 'economic_efficiency' and 'AI-creative_capability' match at cosine 0.457, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency<->AI-productivity_enhancement | Grey zone ruled DROP: 'economic_efficiency' and 'AI-productivity_enhancement' match at cosine 0.677, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency<->AI-productivity_enhancement | Grey zone ruled DROP: 'economic_efficiency' and 'AI-productivity_enhancement' match at cosine 0.720, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency<->AI-productivity_enhancement | Grey zone ruled KEEP: 'economic_efficiency' and 'AI-productivity_enhancement' match at cosine 0.626, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency<->AI-productivity_enhancement | Grey zone ruled KEEP: 'economic_efficiency' and 'AI-productivity_enhancement' match at cosine 0.774, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency<->AI-sector-focus-digital_marketing | Grey zone ruled KEEP: 'economic_efficiency' and 'AI-sector-focus-digital_marketing' match at cosine 0.622, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency<->AI-sector_transformation | Grey zone ruled DROP: 'economic_efficiency' and 'AI-sector_transformation' match at cosine 0.678, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency<->AI-utility | Grey zone ruled DROP: 'economic_efficiency' and 'AI-utility' match at cosine 0.711, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency<->economic_efficiency-cost_reduction | Grey zone ruled DROP: 'economic_efficiency' and 'economic_efficiency-cost_reduction' match at cosine 0.785, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency<->economic_efficiency-logistics | Grey zone ruled DROP: 'economic_efficiency' and 'economic_efficiency-logistics' match at cosine 0.700, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency<->economic_impact-productivity_gain | Grey zone ruled KEEP: 'economic_efficiency' and 'economic_impact-productivity_gain' match at cosine 0.580, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency<->economic_impact-productivity_gain | Grey zone ruled KEEP: 'economic_efficiency' and 'economic_impact-productivity_gain' match at cosine 0.604, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_impact-productivity_gain<->AI-multi-use | Grey zone ruled DROP: 'economic_impact-productivity_gain' and 'AI-multi-use' match at cosine 0.562, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_impact-productivity_gain<->AI-role_expansion | Grey zone ruled KEEP: 'economic_impact-productivity_gain' and 'AI-role_expansion' match at cosine 0.565, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_impact<->education-sector_transformation | Grey zone ruled KEEP: 'economic_impact' and 'education-sector_transformation' match at cosine 0.550, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | education-accessibility<->accessibility-inclusive_education | Grey zone ruled DROP: 'education-accessibility' and 'accessibility-inclusive_education' match at cosine 0.740, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | education-personalised_learning<->education-sector_transformation | Grey zone ruled DROP: 'education-personalised_learning' and 'education-sector_transformation' match at cosine 0.734, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | education-personalised_learning<->education-sector_transformation | Grey zone ruled KEEP: 'education-personalised_learning' and 'education-sector_transformation' match at cosine 0.591, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | education-sector-transformation<->education-sector_transformation | Grey zone ruled DROP: 'education-sector-transformation' and 'education-sector_transformation' match at cosine 0.781, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | education-sector-transformation<->education-sector_transformation | Grey zone ruled KEEP: 'education-sector-transformation' and 'education-sector_transformation' match at cosine 0.645, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | education-sector-transformation<->sector-focus-defence_education | Grey zone ruled DROP: 'education-sector-transformation' and 'sector-focus-defence_education' match at cosine 0.615, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | education<->education-sector_transformation | Grey zone ruled DROP: 'education' and 'education-sector_transformation' match at cosine 0.772, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-job_creation<->employment_transformation-job_creation | Grey zone ruled DROP: 'employment_transformation-job_creation' and 'employment_transformation-job_creation' match at cosine 0.666, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-job_creation<->employment_transformation-job_creation | Grey zone ruled DROP: 'employment_transformation-job_creation' and 'employment_transformation-job_creation' match at cosine 0.756, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-job_creation<->employment_transformation-job_creation | Grey zone ruled KEEP: 'employment_transformation-job_creation' and 'employment_transformation-job_creation' match at cosine 0.701, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-job_creation<->employment_transformation-workforce_retraining | Grey zone ruled KEEP: 'employment_transformation-job_creation' and 'employment_transformation-workforce_retraining' match at cosine 0.618, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-job_displacement<->employment_transformation-job_displacement | Grey zone ruled DROP: 'employment_transformation-job_displacement' and 'employment_transformation-job_displacement' match at cosine 0.671, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-job_displacement<->employment_transformation-job_displacement | Grey zone ruled DROP: 'employment_transformation-job_displacement' and 'employment_transformation-job_displacement' match at cosine 0.722, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-job_displacement<->employment_transformation-job_displacement | Grey zone ruled DROP: 'employment_transformation-job_displacement' and 'employment_transformation-job_displacement' match at cosine 0.725, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-job_displacement<->employment_transformation-job_displacement | Grey zone ruled DROP: 'employment_transformation-job_displacement' and 'employment_transformation-job_displacement' match at cosine 0.768, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-job_displacement<->employment_transformation-job_displacement | Grey zone ruled KEEP: 'employment_transformation-job_displacement' and 'employment_transformation-job_displacement' match at cosine 0.733, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-job_displacement<->negative_impacts-job_destruction | Grey zone ruled DROP: 'employment_transformation-job_displacement' and 'negative_impacts-job_destruction' match at cosine 0.697, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-job_displacement<->negative_impacts-job_destruction | Grey zone ruled DROP: 'employment_transformation-job_displacement' and 'negative_impacts-job_destruction' match at cosine 0.763, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-job_displacement<->negative_impacts-job_destruction | Grey zone ruled KEEP: 'employment_transformation-job_displacement' and 'negative_impacts-job_destruction' match at cosine 0.667, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-job_displacement<->negative_impacts-laziness | Grey zone ruled KEEP: 'employment_transformation-job_displacement' and 'negative_impacts-laziness' match at cosine 0.590, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-job_displacement<->sector-focus-education | Grey zone ruled KEEP: 'employment_transformation-job_displacement' and 'sector-focus-education' match at cosine 0.620, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-new_opportunities<->AI-sector_transformation | Grey zone ruled KEEP: 'employment_transformation-new_opportunities' and 'AI-sector_transformation' match at cosine 0.528, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-workforce_retraining<->employment_transformation-workforce_retraining | Grey zone ruled DROP: 'employment_transformation-workforce_retraining' and 'employment_transformation-workforce_retraining' match at cosine 0.766, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-workforce_retraining<->employment_transformation-workforce_retraining | Grey zone ruled DROP: 'employment_transformation-workforce_retraining' and 'employment_transformation-workforce_retraining' match at cosine 0.767, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation-workforce_retraining<->impact-work_ease | Grey zone ruled KEEP: 'employment_transformation-workforce_retraining' and 'impact-work_ease' match at cosine 0.471, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation<->AI-employment_transformation | Grey zone ruled DROP: 'employment_transformation' and 'AI-employment_transformation' match at cosine 0.653, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation<->complex_problem_solving | Grey zone ruled KEEP: 'employment_transformation' and 'complex_problem_solving' match at cosine 0.480, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation<->economic_efficiency-recession | Grey zone ruled KEEP: 'employment_transformation' and 'economic_efficiency-recession' match at cosine 0.529, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation<->employment_transformation-content_creation | Grey zone ruled DROP: 'employment_transformation' and 'employment_transformation-content_creation' match at cosine 0.679, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation<->employment_transformation-job_creation | Grey zone ruled KEEP: 'employment_transformation' and 'employment_transformation-job_creation' match at cosine 0.681, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation<->employment_transformation-job_displacement | Grey zone ruled DROP: 'employment_transformation' and 'employment_transformation-job_displacement' match at cosine 0.692, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation<->employment_transformation-workforce_retraining | Grey zone ruled KEEP: 'employment_transformation' and 'employment_transformation-workforce_retraining' match at cosine 0.722, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation<->impact-technological_advancement | Grey zone ruled KEEP: 'employment_transformation' and 'impact-technological_advancement' match at cosine 0.636, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation<->impact-work_ease | Grey zone ruled DROP: 'employment_transformation' and 'impact-work_ease' match at cosine 0.768, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation<->labor-competitive_advantage | Grey zone ruled DROP: 'employment_transformation' and 'labor-competitive_advantage' match at cosine 0.594, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation<->negative_impacts-job_destruction | Grey zone ruled DROP: 'employment_transformation' and 'negative_impacts-job_destruction' match at cosine 0.610, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation<->negative_impacts-job_destruction | Grey zone ruled DROP: 'employment_transformation' and 'negative_impacts-job_destruction' match at cosine 0.780, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation<->utility-work_efficiency | Grey zone ruled KEEP: 'employment_transformation' and 'utility-work_efficiency' match at cosine 0.528, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | enhanced-communication<->AI-enhanced-communication | Grey zone ruled DROP: 'enhanced-communication' and 'AI-enhanced-communication' match at cosine 0.735, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | enhanced-communication<->impact-rapid_change | Grey zone ruled KEEP: 'enhanced-communication' and 'impact-rapid_change' match at cosine 0.500, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | global_defence<->AI-omnipotence | Grey zone ruled KEEP: 'global_defence' and 'AI-omnipotence' match at cosine 0.713, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | impact-digital_exclusion<->accessibility-digital_exclusion | Grey zone ruled DROP: 'impact-digital_exclusion' and 'accessibility-digital_exclusion' match at cosine 0.720, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | impact-public_safety<->impact-public_safety | Grey zone ruled KEEP: 'impact-public_safety' and 'impact-public_safety' match at cosine 0.764, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | impact-rapid_change<->impact-rapid_change | Grey zone ruled DROP: 'impact-rapid_change' and 'impact-rapid_change' match at cosine 0.767, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | impact-rapid_change<->society-digital-transformation | Grey zone ruled DROP: 'impact-rapid_change' and 'society-digital-transformation' match at cosine 0.512, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | impact-technological_advancement<->AI-multi_use | Grey zone ruled KEEP: 'impact-technological_advancement' and 'AI-multi_use' match at cosine 0.680, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | impact-technological_advancement<->AI-sector_transformation | Grey zone ruled DROP: 'impact-technological_advancement' and 'AI-sector_transformation' match at cosine 0.563, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | impact-technological_advancement<->impact-technological_advancement | Grey zone ruled DROP: 'impact-technological_advancement' and 'impact-technological_advancement' match at cosine 0.675, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | impact-technological_advancement<->impact-technological_advancement | Grey zone ruled DROP: 'impact-technological_advancement' and 'impact-technological_advancement' match at cosine 0.712, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | impact-technological_advancement<->impact-technological_advancement | Grey zone ruled DROP: 'impact-technological_advancement' and 'impact-technological_advancement' match at cosine 0.765, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | impact-technological_advancement<->impact-technological_advancement | Grey zone ruled DROP: 'impact-technological_advancement' and 'impact-technological_advancement' match at cosine 0.770, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | impact-technological_advancement<->impact-technological_advancement | Grey zone ruled DROP: 'impact-technological_advancement' and 'impact-technological_advancement' match at cosine 0.775, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | impact-technological_advancement<->impact-technological_advancement | Grey zone ruled KEEP: 'impact-technological_advancement' and 'impact-technological_advancement' match at cosine 0.686, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | impact-work_ease<->AI-daily_life_assistance | Grey zone ruled KEEP: 'impact-work_ease' and 'AI-daily_life_assistance' match at cosine 0.796, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | job_displacement<->employment_transformation-job_displacement | Grey zone ruled DROP: 'job_displacement' and 'employment_transformation-job_displacement' match at cosine 0.662, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | job_displacement<->employment_transformation-job_displacement | Grey zone ruled DROP: 'job_displacement' and 'employment_transformation-job_displacement' match at cosine 0.740, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | job_displacement<->negative_impacts-job_destruction | Grey zone ruled DROP: 'job_displacement' and 'negative_impacts-job_destruction' match at cosine 0.659, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | job_displacement<->negative_impacts-job_destruction | Grey zone ruled DROP: 'job_displacement' and 'negative_impacts-job_destruction' match at cosine 0.748, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | job_displacement<->negative_impacts-job_destruction | Grey zone ruled KEEP: 'job_displacement' and 'negative_impacts-job_destruction' match at cosine 0.791, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | labor-job_transformation<->labor-competitive_advantage | Grey zone ruled KEEP: 'labor-job_transformation' and 'labor-competitive_advantage' match at cosine 0.544, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | labor-job_transformation<->negative_impacts-job_destruction | Grey zone ruled KEEP: 'labor-job_transformation' and 'negative_impacts-job_destruction' match at cosine 0.631, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | labor-job_transformation<->negative_impacts-job_destruction | Grey zone ruled KEEP: 'labor-job_transformation' and 'negative_impacts-job_destruction' match at cosine 0.643, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | mindset_shift-problem_identification<->negative_impacts-misuse | Grey zone ruled KEEP: 'mindset_shift-problem_identification' and 'negative_impacts-misuse' match at cosine 0.661, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | mindset_shift<->employment_transformation-workforce_retraining | Grey zone ruled DROP: 'mindset_shift' and 'employment_transformation-workforce_retraining' match at cosine 0.615, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | multi-use<->AI-multi_use | Grey zone ruled DROP: 'multi-use' and 'AI-multi_use' match at cosine 0.630, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | multi-use<->AI-ubiquity | Grey zone ruled DROP: 'multi-use' and 'AI-ubiquity' match at cosine 0.554, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | multi-use<->ai-utility | Grey zone ruled KEEP: 'multi-use' and 'ai-utility' match at cosine 0.528, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | multi-use<->creative_capability-media_generation | Grey zone ruled KEEP: 'multi-use' and 'creative_capability-media_generation' match at cosine 0.523, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | multi-use<->impact-public_safety | Grey zone ruled KEEP: 'multi-use' and 'impact-public_safety' match at cosine 0.658, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | multi-use<->impact-technological_advancement | Grey zone ruled KEEP: 'multi-use' and 'impact-technological_advancement' match at cosine 0.476, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | multi-use<->impact-work_ease | Grey zone ruled KEEP: 'multi-use' and 'impact-work_ease' match at cosine 0.572, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | multi-use<->multi-use | Grey zone ruled DROP: 'multi-use' and 'multi-use' match at cosine 0.769, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | multi_use<->AI-multi_use | Grey zone ruled DROP: 'multi_use' and 'AI-multi_use' match at cosine 0.789, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | multi_use<->multi-use | Grey zone ruled DROP: 'multi_use' and 'multi-use' match at cosine 0.774, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | multi_use<->perception-central_role | Grey zone ruled KEEP: 'multi_use' and 'perception-central_role' match at cosine 0.589, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | need_for_awareness-literacy<->education-literacy_requirement | Grey zone ruled DROP: 'need_for_awareness-literacy' and 'education-literacy_requirement' match at cosine 0.790, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | need_for_awareness<->concern-ethical_development | Grey zone ruled DROP: 'need_for_awareness' and 'concern-ethical_development' match at cosine 0.732, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | need_for_awareness<->concern-ethical_development | Grey zone ruled DROP: 'need_for_awareness' and 'concern-ethical_development' match at cosine 0.748, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | need_for_awareness<->concern-human_dependency | Grey zone ruled DROP: 'need_for_awareness' and 'concern-human_dependency' match at cosine 0.644, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | need_for_awareness<->need_for_awareness-literacy | Grey zone ruled DROP: 'need_for_awareness' and 'need_for_awareness-literacy' match at cosine 0.623, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | need_for_awareness<->need_for_awareness-literacy | Grey zone ruled DROP: 'need_for_awareness' and 'need_for_awareness-literacy' match at cosine 0.715, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | need_for_awareness<->need_for_awareness-literacy | Grey zone ruled DROP: 'need_for_awareness' and 'need_for_awareness-literacy' match at cosine 0.730, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | need_for_awareness<->negative_impacts-human_subjugation | Grey zone ruled KEEP: 'need_for_awareness' and 'negative_impacts-human_subjugation' match at cosine 0.509, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | need_for_awareness<->safety-kill_switch | Grey zone ruled KEEP: 'need_for_awareness' and 'safety-kill_switch' match at cosine 0.485, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-cybersecurity_risks<->concern-cybersecurity | Grey zone ruled DROP: 'negative_impacts-cybersecurity_risks' and 'concern-cybersecurity' match at cosine 0.602, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-dual_nature<->negative_impacts-dual_nature | Grey zone ruled DROP: 'negative_impacts-dual_nature' and 'negative_impacts-dual_nature' match at cosine 0.693, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-dual_nature<->negative_impacts-misuse | Grey zone ruled DROP: 'negative_impacts-dual_nature' and 'negative_impacts-misuse' match at cosine 0.732, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-human_subjugation<->negative_impacts-human_subjugation | Grey zone ruled DROP: 'negative_impacts-human_subjugation' and 'negative_impacts-human_subjugation' match at cosine 0.739, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-human_subjugation<->negative_impacts-misuse | Grey zone ruled KEEP: 'negative_impacts-human_subjugation' and 'negative_impacts-misuse' match at cosine 0.691, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-human_subjugation<->negative_impacts-misuse | Grey zone ruled KEEP: 'negative_impacts-human_subjugation' and 'negative_impacts-misuse' match at cosine 0.732, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-human_subjugation<->negative_impacts-physical_health | Grey zone ruled KEEP: 'negative_impacts-human_subjugation' and 'negative_impacts-physical_health' match at cosine 0.722, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-human_subjugation<->society-social_norms | Grey zone ruled KEEP: 'negative_impacts-human_subjugation' and 'society-social_norms' match at cosine 0.614, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-human_subjugation<->threat-to-humanity | Grey zone ruled KEEP: 'negative_impacts-human_subjugation' and 'threat-to-humanity' match at cosine 0.738, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->concern-human_dependency | Grey zone ruled KEEP: 'negative_impacts-job_destruction' and 'concern-human_dependency' match at cosine 0.695, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->employment_transformation | Grey zone ruled DROP: 'negative_impacts-job_destruction' and 'employment_transformation' match at cosine 0.687, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->negative_impacts-job_destruction | Grey zone ruled DROP: 'negative_impacts-job_destruction' and 'negative_impacts-job_destruction' match at cosine 0.736, between tau_low 0.45 and tau_high 0.80. | 2 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->negative_impacts-job_destruction | Grey zone ruled DROP: 'negative_impacts-job_destruction' and 'negative_impacts-job_destruction' match at cosine 0.738, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->negative_impacts-job_destruction | Grey zone ruled DROP: 'negative_impacts-job_destruction' and 'negative_impacts-job_destruction' match at cosine 0.743, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->negative_impacts-job_destruction | Grey zone ruled DROP: 'negative_impacts-job_destruction' and 'negative_impacts-job_destruction' match at cosine 0.754, between tau_low 0.45 and tau_high 0.80. | 2 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->negative_impacts-job_destruction | Grey zone ruled DROP: 'negative_impacts-job_destruction' and 'negative_impacts-job_destruction' match at cosine 0.756, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->negative_impacts-job_destruction | Grey zone ruled DROP: 'negative_impacts-job_destruction' and 'negative_impacts-job_destruction' match at cosine 0.761, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->negative_impacts-job_destruction | Grey zone ruled DROP: 'negative_impacts-job_destruction' and 'negative_impacts-job_destruction' match at cosine 0.764, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->negative_impacts-job_destruction | Grey zone ruled DROP: 'negative_impacts-job_destruction' and 'negative_impacts-job_destruction' match at cosine 0.795, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->negative_impacts-job_destruction | Grey zone ruled DROP: 'negative_impacts-job_destruction' and 'negative_impacts-job_destruction' match at cosine 0.797, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->negative_impacts-job_destruction | Grey zone ruled DROP: 'negative_impacts-job_destruction' and 'negative_impacts-job_destruction' match at cosine 0.799, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->positive_outcomes-work_relief | Grey zone ruled KEEP: 'negative_impacts-job_destruction' and 'positive_outcomes-work_relief' match at cosine 0.552, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-laziness<->concern-loss_of_effort | Grey zone ruled DROP: 'negative_impacts-laziness' and 'concern-loss_of_effort' match at cosine 0.714, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-laziness<->negative_impacts-laziness | Grey zone ruled DROP: 'negative_impacts-laziness' and 'negative_impacts-laziness' match at cosine 0.766, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-laziness<->negative_impacts-laziness | Grey zone ruled DROP: 'negative_impacts-laziness' and 'negative_impacts-laziness' match at cosine 0.793, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->concern-deepfakes | Grey zone ruled KEEP: 'negative_impacts-misuse' and 'concern-deepfakes' match at cosine 0.519, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->negative_impacts-dual_nature | Grey zone ruled DROP: 'negative_impacts-misuse' and 'negative_impacts-dual_nature' match at cosine 0.716, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->negative_impacts-dual_nature | Grey zone ruled KEEP: 'negative_impacts-misuse' and 'negative_impacts-dual_nature' match at cosine 0.603, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->negative_impacts-human_subjugation | Grey zone ruled KEEP: 'negative_impacts-misuse' and 'negative_impacts-human_subjugation' match at cosine 0.545, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->negative_impacts-laziness | Grey zone ruled KEEP: 'negative_impacts-misuse' and 'negative_impacts-laziness' match at cosine 0.617, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->negative_impacts-laziness | Grey zone ruled KEEP: 'negative_impacts-misuse' and 'negative_impacts-laziness' match at cosine 0.647, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->negative_impacts-misuse | Grey zone ruled DROP: 'negative_impacts-misuse' and 'negative_impacts-misuse' match at cosine 0.686, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->negative_impacts-misuse | Grey zone ruled DROP: 'negative_impacts-misuse' and 'negative_impacts-misuse' match at cosine 0.729, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->negative_impacts-misuse | Grey zone ruled DROP: 'negative_impacts-misuse' and 'negative_impacts-misuse' match at cosine 0.752, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->negative_impacts-misuse | Grey zone ruled DROP: 'negative_impacts-misuse' and 'negative_impacts-misuse' match at cosine 0.755, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->negative_impacts-misuse | Grey zone ruled DROP: 'negative_impacts-misuse' and 'negative_impacts-misuse' match at cosine 0.791, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->risk-malicious_use | Grey zone ruled DROP: 'negative_impacts-misuse' and 'risk-malicious_use' match at cosine 0.736, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts<->negative_impacts-misuse | Grey zone ruled DROP: 'negative_impacts' and 'negative_impacts-misuse' match at cosine 0.712, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | perception-central_role<->AI-role_human_replacement | Grey zone ruled KEEP: 'perception-central_role' and 'AI-role_human_replacement' match at cosine 0.610, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | perception-central_role<->concern-human_dependency | Grey zone ruled KEEP: 'perception-central_role' and 'concern-human_dependency' match at cosine 0.656, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | perception-central_role<->daily_life_assistance-problem_resolution | Grey zone ruled KEEP: 'perception-central_role' and 'daily_life_assistance-problem_resolution' match at cosine 0.697, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | perception-central_role<->negative_impacts-misuse | Grey zone ruled KEEP: 'perception-central_role' and 'negative_impacts-misuse' match at cosine 0.461, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-accessible_healthcare<->AI-sector-focus-health | Grey zone ruled KEEP: 'positive_outcomes-accessible_healthcare' and 'AI-sector-focus-health' match at cosine 0.587, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-accessible_healthcare<->economic_efficiency-productivity_gain | Grey zone ruled KEEP: 'positive_outcomes-accessible_healthcare' and 'economic_efficiency-productivity_gain' match at cosine 0.663, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->AI-positive_outlook | Grey zone ruled KEEP: 'positive_outcomes-work_relief' and 'AI-positive_outlook' match at cosine 0.568, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->AI-utility | Grey zone ruled DROP: 'positive_outcomes-work_relief' and 'AI-utility' match at cosine 0.568, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->AI-utility | Grey zone ruled KEEP: 'positive_outcomes-work_relief' and 'AI-utility' match at cosine 0.617, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->benefit-reduced_stress | Grey zone ruled KEEP: 'positive_outcomes-work_relief' and 'benefit-reduced_stress' match at cosine 0.768, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->economic_impact-universal_basic_income | Grey zone ruled KEEP: 'positive_outcomes-work_relief' and 'economic_impact-universal_basic_income' match at cosine 0.482, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->impact-work_ease | Grey zone ruled DROP: 'positive_outcomes-work_relief' and 'impact-work_ease' match at cosine 0.674, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->impact-work_ease | Grey zone ruled DROP: 'positive_outcomes-work_relief' and 'impact-work_ease' match at cosine 0.676, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->perception-central_role | Grey zone ruled KEEP: 'positive_outcomes-work_relief' and 'perception-central_role' match at cosine 0.528, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->positive_outcomes-work_relief | Grey zone ruled DROP: 'positive_outcomes-work_relief' and 'positive_outcomes-work_relief' match at cosine 0.679, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->utility-work_ease | Grey zone ruled DROP: 'positive_outcomes-work_relief' and 'utility-work_ease' match at cosine 0.696, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->utility-work_efficiency | Grey zone ruled KEEP: 'positive_outcomes-work_relief' and 'utility-work_efficiency' match at cosine 0.562, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes<->impact-technological_advancement | Grey zone ruled KEEP: 'positive_outcomes' and 'impact-technological_advancement' match at cosine 0.713, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook-better_world<->impact-technological_advancement | Grey zone ruled DROP: 'positive_outlook-better_world' and 'impact-technological_advancement' match at cosine 0.662, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook-wealth_and_happiness<->AI-enhanced-communication | Grey zone ruled KEEP: 'positive_outlook-wealth_and_happiness' and 'AI-enhanced-communication' match at cosine 0.722, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook-wealth_and_happiness<->AI-positive_outlook | Grey zone ruled KEEP: 'positive_outlook-wealth_and_happiness' and 'AI-positive_outlook' match at cosine 0.782, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook-wealth_and_happiness<->AI-productivity_enhancement | Grey zone ruled KEEP: 'positive_outlook-wealth_and_happiness' and 'AI-productivity_enhancement' match at cosine 0.541, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook-wealth_and_happiness<->positive_outcomes-work_relief | Grey zone ruled KEEP: 'positive_outlook-wealth_and_happiness' and 'positive_outcomes-work_relief' match at cosine 0.582, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook-wealth_and_happiness<->positive_outlook-wealth_and_happiness | Grey zone ruled DROP: 'positive_outlook-wealth_and_happiness' and 'positive_outlook-wealth_and_happiness' match at cosine 0.786, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook-wealth_and_happiness<->utility-work_ease | Grey zone ruled KEEP: 'positive_outlook-wealth_and_happiness' and 'utility-work_ease' match at cosine 0.635, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook-work_relief<->impact-work_ease | Grey zone ruled KEEP: 'positive_outlook-work_relief' and 'impact-work_ease' match at cosine 0.660, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook-work_relief<->positive_outcomes-work_relief | Grey zone ruled DROP: 'positive_outlook-work_relief' and 'positive_outcomes-work_relief' match at cosine 0.755, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook-work_relief<->positive_outcomes-work_relief | Grey zone ruled KEEP: 'positive_outlook-work_relief' and 'positive_outcomes-work_relief' match at cosine 0.531, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->AI-employment_transformation | Grey zone ruled DROP: 'positive_outlook' and 'AI-employment_transformation' match at cosine 0.728, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->AI-enhanced-communication | Grey zone ruled DROP: 'positive_outlook' and 'AI-enhanced-communication' match at cosine 0.742, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->AI-multi-use | Grey zone ruled KEEP: 'positive_outlook' and 'AI-multi-use' match at cosine 0.663, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->AI-perception-central_role | Grey zone ruled DROP: 'positive_outlook' and 'AI-perception-central_role' match at cosine 0.755, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->AI-productivity_enhancement | Grey zone ruled DROP: 'positive_outlook' and 'AI-productivity_enhancement' match at cosine 0.640, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->AI-productivity_enhancement | Grey zone ruled KEEP: 'positive_outlook' and 'AI-productivity_enhancement' match at cosine 0.581, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->AI-productivity_enhancement | Grey zone ruled KEEP: 'positive_outlook' and 'AI-productivity_enhancement' match at cosine 0.687, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->AI-utility | Grey zone ruled KEEP: 'positive_outlook' and 'AI-utility' match at cosine 0.729, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->ai-dependence-lifestyle | Grey zone ruled KEEP: 'positive_outlook' and 'ai-dependence-lifestyle' match at cosine 0.573, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->ai-productivity_enhancement | Grey zone ruled KEEP: 'positive_outlook' and 'ai-productivity_enhancement' match at cosine 0.670, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->dependence-lifestyle | Grey zone ruled DROP: 'positive_outlook' and 'dependence-lifestyle' match at cosine 0.656, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->economic_efficiency | Grey zone ruled KEEP: 'positive_outlook' and 'economic_efficiency' match at cosine 0.612, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->employment_transformation | Grey zone ruled KEEP: 'positive_outlook' and 'employment_transformation' match at cosine 0.602, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->employment_transformation-workforce_retraining | Grey zone ruled KEEP: 'positive_outlook' and 'employment_transformation-workforce_retraining' match at cosine 0.648, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-enhanced-communication | Grey zone ruled KEEP: 'positive_outlook' and 'impact-enhanced-communication' match at cosine 0.622, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-public_safety | Grey zone ruled KEEP: 'positive_outlook' and 'impact-public_safety' match at cosine 0.470, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-technological_advancement | Grey zone ruled DROP: 'positive_outlook' and 'impact-technological_advancement' match at cosine 0.585, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-technological_advancement | Grey zone ruled DROP: 'positive_outlook' and 'impact-technological_advancement' match at cosine 0.589, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-technological_advancement | Grey zone ruled DROP: 'positive_outlook' and 'impact-technological_advancement' match at cosine 0.722, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-technological_advancement | Grey zone ruled KEEP: 'positive_outlook' and 'impact-technological_advancement' match at cosine 0.454, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-technological_advancement | Grey zone ruled KEEP: 'positive_outlook' and 'impact-technological_advancement' match at cosine 0.507, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-technological_advancement | Grey zone ruled KEEP: 'positive_outlook' and 'impact-technological_advancement' match at cosine 0.563, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-technological_advancement | Grey zone ruled KEEP: 'positive_outlook' and 'impact-technological_advancement' match at cosine 0.570, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-technological_advancement | Grey zone ruled KEEP: 'positive_outlook' and 'impact-technological_advancement' match at cosine 0.615, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-technological_advancement | Grey zone ruled KEEP: 'positive_outlook' and 'impact-technological_advancement' match at cosine 0.641, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-technological_advancement | Grey zone ruled KEEP: 'positive_outlook' and 'impact-technological_advancement' match at cosine 0.703, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-technological_advancement | Grey zone ruled KEEP: 'positive_outlook' and 'impact-technological_advancement' match at cosine 0.773, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-work_ease | Grey zone ruled KEEP: 'positive_outlook' and 'impact-work_ease' match at cosine 0.568, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-work_ease | Grey zone ruled KEEP: 'positive_outlook' and 'impact-work_ease' match at cosine 0.592, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->labor-free_workforce | Grey zone ruled KEEP: 'positive_outlook' and 'labor-free_workforce' match at cosine 0.618, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->mindset_shift-problem_identification | Grey zone ruled KEEP: 'positive_outlook' and 'mindset_shift-problem_identification' match at cosine 0.682, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->negative_impacts-dual_nature | Grey zone ruled KEEP: 'positive_outlook' and 'negative_impacts-dual_nature' match at cosine 0.592, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->negative_impacts-misuse | Grey zone ruled KEEP: 'positive_outlook' and 'negative_impacts-misuse' match at cosine 0.605, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outcomes-medical_intervention | Grey zone ruled DROP: 'positive_outlook' and 'positive_outcomes-medical_intervention' match at cosine 0.715, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outcomes-work_relief | Grey zone ruled DROP: 'positive_outlook' and 'positive_outcomes-work_relief' match at cosine 0.638, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outcomes-work_relief | Grey zone ruled DROP: 'positive_outlook' and 'positive_outcomes-work_relief' match at cosine 0.700, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outcomes-work_relief | Grey zone ruled KEEP: 'positive_outlook' and 'positive_outcomes-work_relief' match at cosine 0.709, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outlook | Grey zone ruled DROP: 'positive_outlook' and 'positive_outlook' match at cosine 0.652, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outlook | Grey zone ruled DROP: 'positive_outlook' and 'positive_outlook' match at cosine 0.700, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outlook | Grey zone ruled DROP: 'positive_outlook' and 'positive_outlook' match at cosine 0.727, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outlook | Grey zone ruled DROP: 'positive_outlook' and 'positive_outlook' match at cosine 0.784, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outlook | Grey zone ruled DROP: 'positive_outlook' and 'positive_outlook' match at cosine 0.799, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outlook | Grey zone ruled KEEP: 'positive_outlook' and 'positive_outlook' match at cosine 0.734, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outlook-wealth_and_happiness | Grey zone ruled DROP: 'positive_outlook' and 'positive_outlook-wealth_and_happiness' match at cosine 0.710, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outlook-wealth_and_happiness | Grey zone ruled KEEP: 'positive_outlook' and 'positive_outlook-wealth_and_happiness' match at cosine 0.737, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outlook-wealth_and_happiness | Grey zone ruled KEEP: 'positive_outlook' and 'positive_outlook-wealth_and_happiness' match at cosine 0.741, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outlook-work_relief | Grey zone ruled DROP: 'positive_outlook' and 'positive_outlook-work_relief' match at cosine 0.596, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outlook-work_relief | Grey zone ruled KEEP: 'positive_outlook' and 'positive_outlook-work_relief' match at cosine 0.676, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outlook-work_relief | Grey zone ruled KEEP: 'positive_outlook' and 'positive_outlook-work_relief' match at cosine 0.778, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->society-digital-transformation | Grey zone ruled KEEP: 'positive_outlook' and 'society-digital-transformation' match at cosine 0.685, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->utility-work_efficiency | Grey zone ruled KEEP: 'positive_outlook' and 'utility-work_efficiency' match at cosine 0.493, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | privacy_security<->concern-privacy_security | Grey zone ruled DROP: 'privacy_security' and 'concern-privacy_security' match at cosine 0.683, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | privacy_security<->concern-privacy_security | Grey zone ruled DROP: 'privacy_security' and 'concern-privacy_security' match at cosine 0.741, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.707, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.756, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | robotics_engineering<->robotics_engineering-medical_assistance | Grey zone ruled DROP: 'robotics_engineering' and 'robotics_engineering-medical_assistance' match at cosine 0.566, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | role-human_replacement<->AI-role_human_replacement | Grey zone ruled DROP: 'role-human_replacement' and 'AI-role_human_replacement' match at cosine 0.682, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | role_human_replacement<->AI-productivity_enhancement | Grey zone ruled KEEP: 'role_human_replacement' and 'AI-productivity_enhancement' match at cosine 0.573, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | safety-improvements-shelter_security<->facilitated-collaboration | Grey zone ruled KEEP: 'safety-improvements-shelter_security' and 'facilitated-collaboration' match at cosine 0.651, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | safety-reduced_accidents<->impact-technological_advancement | Grey zone ruled KEEP: 'safety-reduced_accidents' and 'impact-technological_advancement' match at cosine 0.582, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | safety-reduced_accidents<->safety-reduced_accidents | Grey zone ruled DROP: 'safety-reduced_accidents' and 'safety-reduced_accidents' match at cosine 0.667, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | safety-reduced_accidents<->safety-reduced_accidents | Grey zone ruled DROP: 'safety-reduced_accidents' and 'safety-reduced_accidents' match at cosine 0.682, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | safety-reduced_accidents<->safety-reduced_accidents | Grey zone ruled DROP: 'safety-reduced_accidents' and 'safety-reduced_accidents' match at cosine 0.717, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-cyber_security<->AI-data-driven | Grey zone ruled DROP: 'sector-focus-cyber_security' and 'AI-data-driven' match at cosine 0.617, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-cyber_security<->sector-focus-cyber_security | Grey zone ruled DROP: 'sector-focus-cyber_security' and 'sector-focus-cyber_security' match at cosine 0.707, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-cyber_security<->sector-focus-cyber_security | Grey zone ruled DROP: 'sector-focus-cyber_security' and 'sector-focus-cyber_security' match at cosine 0.752, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-cyber_security<->security | Grey zone ruled DROP: 'sector-focus-cyber_security' and 'security' match at cosine 0.760, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-digital_marketing<->AI-productivity_enhancement | Grey zone ruled KEEP: 'sector-focus-digital_marketing' and 'AI-productivity_enhancement' match at cosine 0.727, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-digital_marketing<->AI-sector-focus-transportation | Grey zone ruled KEEP: 'sector-focus-digital_marketing' and 'AI-sector-focus-transportation' match at cosine 0.765, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-digital_marketing<->sector-focus-education | Grey zone ruled KEEP: 'sector-focus-digital_marketing' and 'sector-focus-education' match at cosine 0.610, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-digital_marketing<->sector-transformation | Grey zone ruled DROP: 'sector-focus-digital_marketing' and 'sector-transformation' match at cosine 0.699, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-digital_marketing<->transportation-navigation_assistance | Grey zone ruled KEEP: 'sector-focus-digital_marketing' and 'transportation-navigation_assistance' match at cosine 0.492, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-education<->impact-technological_advancement | Grey zone ruled KEEP: 'sector-focus-education' and 'impact-technological_advancement' match at cosine 0.609, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-education<->sector-focus-education | Grey zone ruled DROP: 'sector-focus-education' and 'sector-focus-education' match at cosine 0.776, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-health<->AI-sector-focus-health | Grey zone ruled DROP: 'sector-focus-health' and 'AI-sector-focus-health' match at cosine 0.673, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-health<->AI-sector-focus-health | Grey zone ruled DROP: 'sector-focus-health' and 'AI-sector-focus-health' match at cosine 0.687, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-health<->AI-sector-focus-health | Grey zone ruled DROP: 'sector-focus-health' and 'AI-sector-focus-health' match at cosine 0.709, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-health<->AI-sector-focus-health | Grey zone ruled DROP: 'sector-focus-health' and 'AI-sector-focus-health' match at cosine 0.723, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-health<->complex_problem_solving-scientific_discovery | Grey zone ruled DROP: 'sector-focus-health' and 'complex_problem_solving-scientific_discovery' match at cosine 0.596, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-health<->sector-focus-health | Grey zone ruled DROP: 'sector-focus-health' and 'sector-focus-health' match at cosine 0.700, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-health<->sector-focus-health | Grey zone ruled DROP: 'sector-focus-health' and 'sector-focus-health' match at cosine 0.704, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-health<->sector-focus-health | Grey zone ruled DROP: 'sector-focus-health' and 'sector-focus-health' match at cosine 0.733, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-health<->sector-focus-health | Grey zone ruled DROP: 'sector-focus-health' and 'sector-focus-health' match at cosine 0.746, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-health<->sector-focus-health | Grey zone ruled DROP: 'sector-focus-health' and 'sector-focus-health' match at cosine 0.780, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector_transformation<->AI-sector_transformation | Grey zone ruled KEEP: 'sector_transformation' and 'AI-sector_transformation' match at cosine 0.615, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector_transformation<->multi_use | Grey zone ruled KEEP: 'sector_transformation' and 'multi_use' match at cosine 0.608, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector_transformation<->sector-focus-real_estate | Grey zone ruled KEEP: 'sector_transformation' and 'sector-focus-real_estate' match at cosine 0.703, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector_transformation<->sector-transformation-industrial | Grey zone ruled DROP: 'sector_transformation' and 'sector-transformation-industrial' match at cosine 0.800, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | society-digital-transformation<->impact-communication_enhancement | Grey zone ruled KEEP: 'society-digital-transformation' and 'impact-communication_enhancement' match at cosine 0.578, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | society-digital-transformation<->impact-rapid_change | Grey zone ruled KEEP: 'society-digital-transformation' and 'impact-rapid_change' match at cosine 0.530, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | society-social_norms<->AI-multi_use | Grey zone ruled KEEP: 'society-social_norms' and 'AI-multi_use' match at cosine 0.598, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | society-social_norms<->negative_impacts-social_isolation | Grey zone ruled DROP: 'society-social_norms' and 'negative_impacts-social_isolation' match at cosine 0.684, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | society-social_norms<->society-social_norms | Grey zone ruled DROP: 'society-social_norms' and 'society-social_norms' match at cosine 0.585, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | threat-to-humanity<->AI-superintelligence | Grey zone ruled KEEP: 'threat-to-humanity' and 'AI-superintelligence' match at cosine 0.774, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | threat-to-humanity<->AI-superintelligence | Grey zone ruled KEEP: 'threat-to-humanity' and 'AI-superintelligence' match at cosine 0.788, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | threat-to-humanity<->negative_impacts-human_subjugation | Grey zone ruled DROP: 'threat-to-humanity' and 'negative_impacts-human_subjugation' match at cosine 0.748, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | threat-to-humanity<->negative_impacts-human_subjugation | Grey zone ruled KEEP: 'threat-to-humanity' and 'negative_impacts-human_subjugation' match at cosine 0.552, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | threat-to-humanity<->negative_impacts-misuse | Grey zone ruled KEEP: 'threat-to-humanity' and 'negative_impacts-misuse' match at cosine 0.639, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | threat-to-humanity<->negative_impacts-misuse | Grey zone ruled KEEP: 'threat-to-humanity' and 'negative_impacts-misuse' match at cosine 0.766, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | threat-to-humanity<->threat-to-humanity | Grey zone ruled DROP: 'threat-to-humanity' and 'threat-to-humanity' match at cosine 0.796, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | transportation-autonomous_vehicles<->transport_impact-autonomous_vehicles | Grey zone ruled DROP: 'transportation-autonomous_vehicles' and 'transport_impact-autonomous_vehicles' match at cosine 0.722, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | transportation-autonomous_vehicles<->transportation-autonomous_vehicles | Grey zone ruled DROP: 'transportation-autonomous_vehicles' and 'transportation-autonomous_vehicles' match at cosine 0.544, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | transportation-autonomous_vehicles<->transportation-autonomous_vehicles | Grey zone ruled DROP: 'transportation-autonomous_vehicles' and 'transportation-autonomous_vehicles' match at cosine 0.589, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | transportation-autonomous_vehicles<->transportation-autonomous_vehicles | Grey zone ruled DROP: 'transportation-autonomous_vehicles' and 'transportation-autonomous_vehicles' match at cosine 0.606, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | transportation-autonomous_vehicles<->transportation-autonomous_vehicles | Grey zone ruled DROP: 'transportation-autonomous_vehicles' and 'transportation-autonomous_vehicles' match at cosine 0.667, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | transportation-autonomous_vehicles<->transportation-autonomous_vehicles | Grey zone ruled DROP: 'transportation-autonomous_vehicles' and 'transportation-autonomous_vehicles' match at cosine 0.731, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | transportation-autonomous_vehicles<->transportation-navigation_assistance | Grey zone ruled DROP: 'transportation-autonomous_vehicles' and 'transportation-navigation_assistance' match at cosine 0.722, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->AI-creative_capability | Grey zone ruled KEEP: 'ubiquity' and 'AI-creative_capability' match at cosine 0.669, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->AI-perception-central_role | Grey zone ruled DROP: 'ubiquity' and 'AI-perception-central_role' match at cosine 0.677, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->AI-productivity_enhancement | Grey zone ruled KEEP: 'ubiquity' and 'AI-productivity_enhancement' match at cosine 0.569, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->AI-role-expansion | Grey zone ruled KEEP: 'ubiquity' and 'AI-role-expansion' match at cosine 0.651, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->AI-ubiquity | Grey zone ruled DROP: 'ubiquity' and 'AI-ubiquity' match at cosine 0.721, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->AI-ubiquity | Grey zone ruled DROP: 'ubiquity' and 'AI-ubiquity' match at cosine 0.725, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->AI-ubiquity | Grey zone ruled DROP: 'ubiquity' and 'AI-ubiquity' match at cosine 0.729, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->AI-ubiquity | Grey zone ruled KEEP: 'ubiquity' and 'AI-ubiquity' match at cosine 0.643, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->AI-ubiquity | Grey zone ruled KEEP: 'ubiquity' and 'AI-ubiquity' match at cosine 0.770, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->ai-dependence-lifestyle | Grey zone ruled DROP: 'ubiquity' and 'ai-dependence-lifestyle' match at cosine 0.706, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->impact-digital_connectivity | Grey zone ruled DROP: 'ubiquity' and 'impact-digital_connectivity' match at cosine 0.757, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->impact-rapid_change | Grey zone ruled DROP: 'ubiquity' and 'impact-rapid_change' match at cosine 0.672, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->impact-rapid_change | Grey zone ruled KEEP: 'ubiquity' and 'impact-rapid_change' match at cosine 0.652, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->labor-competitive_advantage | Grey zone ruled KEEP: 'ubiquity' and 'labor-competitive_advantage' match at cosine 0.498, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->multi_use-universal_application | Grey zone ruled DROP: 'ubiquity' and 'multi_use-universal_application' match at cosine 0.694, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->need_for_awareness-literacy | Grey zone ruled KEEP: 'ubiquity' and 'need_for_awareness-literacy' match at cosine 0.708, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->perception-central_role | Grey zone ruled KEEP: 'ubiquity' and 'perception-central_role' match at cosine 0.788, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->sector-focus-transportation | Grey zone ruled KEEP: 'ubiquity' and 'sector-focus-transportation' match at cosine 0.607, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->transportation-autonomous_vehicles | Grey zone ruled KEEP: 'ubiquity' and 'transportation-autonomous_vehicles' match at cosine 0.544, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->ubiquity | Grey zone ruled DROP: 'ubiquity' and 'ubiquity' match at cosine 0.630, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->ubiquity | Grey zone ruled DROP: 'ubiquity' and 'ubiquity' match at cosine 0.632, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->ubiquity | Grey zone ruled DROP: 'ubiquity' and 'ubiquity' match at cosine 0.715, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->ubiquity | Grey zone ruled DROP: 'ubiquity' and 'ubiquity' match at cosine 0.725, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->ubiquity | Grey zone ruled DROP: 'ubiquity' and 'ubiquity' match at cosine 0.726, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->ubiquity | Grey zone ruled DROP: 'ubiquity' and 'ubiquity' match at cosine 0.731, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->ubiquity | Grey zone ruled DROP: 'ubiquity' and 'ubiquity' match at cosine 0.733, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->ubiquity | Grey zone ruled KEEP: 'ubiquity' and 'ubiquity' match at cosine 0.793, between tau_low 0.45 and tau_high 0.80. | 2 |
| M1 | WARN | grey_zone_judged | unclear_outputs<->mindset_shift | Grey zone ruled KEEP: 'unclear_outputs' and 'mindset_shift' match at cosine 0.589, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | user_experience_relaxation<->experience-convenience_of_travel | Grey zone ruled DROP: 'user_experience_relaxation' and 'experience-convenience_of_travel' match at cosine 0.681, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | user_experience_relaxation<->user_experience_relaxation | Grey zone ruled DROP: 'user_experience_relaxation' and 'user_experience_relaxation' match at cosine 0.742, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility-work_ease<->AI-utility | Grey zone ruled KEEP: 'utility-work_ease' and 'AI-utility' match at cosine 0.579, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility-work_ease<->automation_of_repetitive_tasks-inventory_management | Grey zone ruled DROP: 'utility-work_ease' and 'automation_of_repetitive_tasks-inventory_management' match at cosine 0.642, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility-work_ease<->automation_of_repetitive_tasks-time_saving | Grey zone ruled KEEP: 'utility-work_ease' and 'automation_of_repetitive_tasks-time_saving' match at cosine 0.572, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility-work_ease<->benefit-reduced_stress | Grey zone ruled KEEP: 'utility-work_ease' and 'benefit-reduced_stress' match at cosine 0.745, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility-work_ease<->enhanced-communication | Grey zone ruled KEEP: 'utility-work_ease' and 'enhanced-communication' match at cosine 0.478, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility-work_ease<->impact-work_ease | Grey zone ruled DROP: 'utility-work_ease' and 'impact-work_ease' match at cosine 0.737, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility-work_ease<->impact-work_ease | Grey zone ruled DROP: 'utility-work_ease' and 'impact-work_ease' match at cosine 0.780, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility-work_ease<->utility-work_ease | Grey zone ruled DROP: 'utility-work_ease' and 'utility-work_ease' match at cosine 0.754, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility-work_ease<->utility-work_ease | Grey zone ruled DROP: 'utility-work_ease' and 'utility-work_ease' match at cosine 0.773, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility-work_ease<->utility-work_ease | Grey zone ruled DROP: 'utility-work_ease' and 'utility-work_ease' match at cosine 0.800, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility-work_ease<->utility-work_ease | Grey zone ruled KEEP: 'utility-work_ease' and 'utility-work_ease' match at cosine 0.783, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility-work_ease<->utility-work_efficiency | Grey zone ruled DROP: 'utility-work_ease' and 'utility-work_efficiency' match at cosine 0.659, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility-work_ease<->utility-work_efficiency | Grey zone ruled DROP: 'utility-work_ease' and 'utility-work_efficiency' match at cosine 0.665, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility-work_efficiency<->AI-productivity_enhancement | Grey zone ruled KEEP: 'utility-work_efficiency' and 'AI-productivity_enhancement' match at cosine 0.620, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility<->AI-daily_life_assistance | Grey zone ruled DROP: 'utility' and 'AI-daily_life_assistance' match at cosine 0.760, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility<->AI-multi_use | Grey zone ruled KEEP: 'utility' and 'AI-multi_use' match at cosine 0.777, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility<->AI-productivity_enhancement | Grey zone ruled KEEP: 'utility' and 'AI-productivity_enhancement' match at cosine 0.747, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility<->ai-utility | Grey zone ruled DROP: 'utility' and 'ai-utility' match at cosine 0.716, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility<->complex_problem_solving-advance_analysis | Grey zone ruled KEEP: 'utility' and 'complex_problem_solving-advance_analysis' match at cosine 0.451, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility<->complex_problem_solving-scientific_discovery | Grey zone ruled KEEP: 'utility' and 'complex_problem_solving-scientific_discovery' match at cosine 0.473, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | utility<->utility-work_ease | Grey zone ruled KEEP: 'utility' and 'utility-work_ease' match at cosine 0.780, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | workforce_retraining<->employment_transformation-workforce_retraining | Grey zone ruled DROP: 'workforce_retraining' and 'employment_transformation-workforce_retraining' match at cosine 0.745, between tau_low 0.45 and tau_high 0.80. | 1 |
| M2 | WARN | route_judge | *message withheld: shares wording with a response* | *message withheld: shares wording with a response* | 12 |
| M2 | WARN | route_judge | *message withheld: shares wording with a response* | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.610, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | *message withheld: shares wording with a response* | Routes JUDGE against 'education-sector-transformation' at cosine 0.773, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | *message withheld: shares wording with a response* | Routes JUDGE against 'impact-work_ease' at cosine 0.593, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | *message withheld: shares wording with a response* | Routes JUDGE against 'positive_outcomes-accessible_healthcare' at cosine 0.724, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | *message withheld: shares wording with a response* | Routes JUDGE against 'ubiquity' at cosine 0.683, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-assistance_for_disabled | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.663, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-automation_of_repetitive_tasks' at cosine 0.672, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-automation_of_repetitive_tasks' at cosine 0.693, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-automation_of_repetitive_tasks' at cosine 0.702, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-automation_of_repetitive_tasks' at cosine 0.722, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-automation_of_repetitive_tasks' at cosine 0.723, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-automation_of_repetitive_tasks' at cosine 0.739, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-multi-use' at cosine 0.681, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.695, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.661, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.773, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.781, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.785, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-sector-focus-transportation' at cosine 0.756, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-transportation-autonomous_vehicles' at cosine 0.721, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'impact-work_ease' at cosine 0.653, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'utility-work_ease' at cosine 0.644, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-behavioral_influence | Routes JUDGE against 'AI-behavioral_influence' at cosine 0.693, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-behavioral_influence | Routes JUDGE against 'impact-communication_enhancement' at cosine 0.612, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-behavioral_influence | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.680, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-complex_problem_solving | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.554, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-creative_capability | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.597, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-creative_capability | Routes JUDGE against 'ai-productivity_enhancement' at cosine 0.616, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-creative_capability | Routes JUDGE against 'creative_capability' at cosine 0.693, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-creative_capability | Routes JUDGE against 'creative_capability' at cosine 0.730, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-creative_capability | Routes JUDGE against 'creative_capability' at cosine 0.790, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-daily_life_assistance | Routes JUDGE against 'ai-utility' at cosine 0.717, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-daily_life_assistance | Routes JUDGE against 'ai-utility' at cosine 0.719, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-daily_life_assistance | Routes JUDGE against 'daily_life_assistance' at cosine 0.750, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-daily_life_assistance | Routes JUDGE against 'daily_life_assistance-automated_payments' at cosine 0.658, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-daily_life_assistance | Routes JUDGE against 'daily_life_assistance-automated_payments' at cosine 0.737, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-daily_life_assistance | Routes JUDGE against 'daily_life_assistance-automated_payments' at cosine 0.750, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-daily_life_assistance | Routes JUDGE against 'daily_life_assistance-automated_payments' at cosine 0.759, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-daily_life_assistance | Routes JUDGE against 'daily_life_assistance-problem_resolution' at cosine 0.706, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-daily_life_assistance | Routes JUDGE against 'daily_life_assistance-problem_resolution' at cosine 0.793, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-daily_life_assistance | Routes JUDGE against 'utility' at cosine 0.759, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-data-driven | Routes JUDGE against 'AI-data-driven' at cosine 0.716, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-data-driven | Routes JUDGE against 'AI-data-driven' at cosine 0.734, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-data-driven | Routes JUDGE against 'AI-data-driven' at cosine 0.767, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-data-driven | Routes JUDGE against 'AI-data_driven' at cosine 0.603, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-data-driven | Routes JUDGE against 'AI-data_driven' at cosine 0.644, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-data-driven | Routes JUDGE against 'AI-omnipotence' at cosine 0.611, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-data_driven | Routes JUDGE against 'AI-dependence-lifestyle' at cosine 0.551, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-dependence-lifestyle | Routes JUDGE against 'ai-dependence-lifestyle' at cosine 0.735, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-dependence-lifestyle | Routes JUDGE against 'dependence-lifestyle' at cosine 0.793, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-disaster_management | Routes JUDGE against 'impact-work_ease' at cosine 0.605, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-divine_connection | Routes JUDGE against 'AI-enhanced-communication' at cosine 0.719, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-economic_efficiency | Routes JUDGE against 'AI-economic_strengthening' at cosine 0.767, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-economic_efficiency | Routes JUDGE against 'complex_problem_solving' at cosine 0.716, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-economic_strengthening | Routes JUDGE against 'impact-technological_advancement' at cosine 0.628, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-efficiency | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.786, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-employment_transformation | Routes JUDGE against 'AI-economic_strengthening' at cosine 0.629, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-employment_transformation | Routes JUDGE against 'employment_transformation-job_displacement' at cosine 0.706, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-employment_transformation | Routes JUDGE against 'employment_transformation-job_displacement' at cosine 0.724, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-enhanced-communication | Routes JUDGE against 'AI-enhanced-communication' at cosine 0.660, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-enhanced-communication | Routes JUDGE against 'AI-sector-focus-digital_marketing' at cosine 0.610, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-entrepreneurial-support | Routes JUDGE against 'AI-perception-central_role' at cosine 0.637, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-facilitated-collaboration | Routes JUDGE against 'AI-impact-immigration' at cosine 0.569, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-global_defence | Routes JUDGE against 'AI-global_defence' at cosine 0.692, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-global_defence | Routes JUDGE against 'impact-technological_advancement' at cosine 0.521, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-impact-immigration | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.587, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-impact-positive_outlook | Routes JUDGE against 'AI-positive_outlook' at cosine 0.752, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-impact-rapid_change | Routes JUDGE against 'impact-technological_advancement' at cosine 0.688, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-impact-women_safety | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.615, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-mindset_shift | Routes JUDGE against 'AI-need_for_awareness' at cosine 0.602, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-multi-use | Routes JUDGE against 'AI-multi-use' at cosine 0.698, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-multi-use | Routes JUDGE against 'AI-multi-use' at cosine 0.781, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-multi-use | Routes JUDGE against 'AI-multi-use' at cosine 0.791, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-multi-use | Routes JUDGE against 'AI-multi-use' at cosine 0.793, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-multi-use | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.701, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-multi_use | Routes JUDGE against 'AI-multi-use' at cosine 0.689, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-multi_use | Routes JUDGE against 'AI-multi-use' at cosine 0.722, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-multi_use | Routes JUDGE against 'AI-multi-use' at cosine 0.741, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-multi_use | Routes JUDGE against 'AI-multi-use' at cosine 0.760, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-multi_use | Routes JUDGE against 'AI-multi-use' at cosine 0.797, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-multi_use | Routes JUDGE against 'AI-multi-use' at cosine 0.799, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-multi_use | Routes JUDGE against 'AI-multi_use' at cosine 0.761, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-need_for_awareness | Routes JUDGE against 'AI-need_for_awareness' at cosine 0.620, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-need_for_awareness | Routes JUDGE against 'AI-need_for_awareness' at cosine 0.641, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-need_for_awareness | Routes JUDGE against 'AI-need_for_awareness' at cosine 0.723, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-need_for_awareness | Routes JUDGE against 'need_for_awareness-literacy' at cosine 0.668, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-need_for_awareness | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.524, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-omnipotence | Routes JUDGE against 'AI-omnipotence' at cosine 0.728, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-omnipotence | Routes JUDGE against 'AI-omnipotence' at cosine 0.747, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-omnipotence | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.664, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-omnipotence | Routes JUDGE against 'ubiquity' at cosine 0.741, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-perception-central_role | Routes JUDGE against 'AI-perception-central_role' at cosine 0.720, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-perception-central_role | Routes JUDGE against 'AI-perception-central_role' at cosine 0.724, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-perception-central_role | Routes JUDGE against 'AI-perception-central_role' at cosine 0.778, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-perception-central_role | Routes JUDGE against 'AI-positive_outlook' at cosine 0.542, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-positive_outlook | Routes JUDGE against 'AI-positive_outlook' at cosine 0.643, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-positive_outlook | Routes JUDGE against 'AI-positive_outlook' at cosine 0.747, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-positive_outlook | Routes JUDGE against 'AI-positive_outlook' at cosine 0.763, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-positive_outlook | Routes JUDGE against 'AI-positive_outlook' at cosine 0.780, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.783, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'AI-entrepreneurial-support' at cosine 0.736, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'AI-entrepreneurial-support' at cosine 0.741, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'AI-entrepreneurial-support' at cosine 0.773, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'AI-multi-use' at cosine 0.766, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.742, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.774, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.781, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.675, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'ai-productivity_enhancement' at cosine 0.720, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'ai-productivity_enhancement' at cosine 0.722, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'ai-productivity_enhancement' at cosine 0.733, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'daily_life_assistance-problem_resolution' at cosine 0.758, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'economic_efficiency-productivity_gain' at cosine 0.733, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'economic_impact-productivity_gain' at cosine 0.597, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'economic_impact-productivity_gain' at cosine 0.674, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'impact-work_ease' at cosine 0.693, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'impact-work_ease' at cosine 0.720, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'utility' at cosine 0.733, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-robotics_engineering | Routes JUDGE against 'AI-robotics_engineering' at cosine 0.596, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-robotics_engineering | Routes JUDGE against 'sector-focus-digital_marketing' at cosine 0.735, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role-expansion | Routes JUDGE against 'AI-role-expansion' at cosine 0.638, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role-expansion | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.624, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role-expansion | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.746, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role-expansion | Routes JUDGE against 'AI-role_human_replacement' at cosine 0.691, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role-human_replacement | Routes JUDGE against 'AI-employment_transformation' at cosine 0.717, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role-human_replacement | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.615, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role-human_replacement | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.798, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role_expansion | Routes JUDGE against 'AI-automation_of_repetitive_tasks' at cosine 0.608, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role_expansion | Routes JUDGE against 'AI-entrepreneurial-support' at cosine 0.685, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role_human_replacement | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.659, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role_human_replacement | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.711, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role_human_replacement | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.764, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role_human_replacement | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.778, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role_human_replacement | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.784, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role_human_replacement | Routes JUDGE against 'role_human_replacement' at cosine 0.653, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector-focus-cyber_security | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.460, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector-focus-defence_education | Routes JUDGE against 'AI-daily_life_assistance' at cosine 0.487, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector-focus-defence_education | Routes JUDGE against 'AI-sector-focus-defence_education' at cosine 0.789, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector-focus-digital_marketing | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.506, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector-focus-digital_marketing | Routes JUDGE against 'AI-sector-focus-digital_marketing' at cosine 0.768, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector-focus-health | Routes JUDGE against 'AI-sector-focus-defence_education' at cosine 0.720, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector-focus-health | Routes JUDGE against 'AI-sector-focus-health' at cosine 0.662, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector-focus-health | Routes JUDGE against 'sector-focus-health' at cosine 0.769, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector-focus-transportation | Routes JUDGE against 'AI-transportation-autonomous_vehicles' at cosine 0.743, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector-focus-transportation | Routes JUDGE against 'sector-focus-transportation' at cosine 0.793, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-sector_transformation | Routes JUDGE against 'AI-sector-focus-defence_education' at cosine 0.641, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector_transformation | Routes JUDGE against 'AI-sector_transformation' at cosine 0.732, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector_transformation | Routes JUDGE against 'AI-sector_transformation' at cosine 0.743, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector_transformation | Routes JUDGE against 'AI-sector_transformation' at cosine 0.744, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector_transformation | Routes JUDGE against 'sector_transformation' at cosine 0.691, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector_transformation | Routes JUDGE against 'sector_transformation' at cosine 0.764, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-superintelligence | Routes JUDGE against 'AI-omnipotence' at cosine 0.650, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-superintelligence | Routes JUDGE against 'AI-superintelligence' at cosine 0.713, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-superintelligence | Routes JUDGE against 'negative_impacts-human_subjugation' at cosine 0.764, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-threat-to-humanity | Routes JUDGE against 'concern-human_dependency' at cosine 0.655, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-transportation-autonomous_vehicles | Routes JUDGE against 'utility-work_ease' at cosine 0.652, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'AI-perception-central_role' at cosine 0.577, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.650, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.697, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.773, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.783, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.785, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.786, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'impact-technological_advancement' at cosine 0.664, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'ubiquity' at cosine 0.715, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'ubiquity' at cosine 0.733, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'ubiquity' at cosine 0.745, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'utility' at cosine 0.778, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-utility | *message withheld: shares wording with a response* | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'AI-daily_life_assistance' at cosine 0.710, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.747, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.760, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'AI-utility' at cosine 0.655, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'AI-utility' at cosine 0.708, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'AI-utility' at cosine 0.769, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'AI-utility' at cosine 0.777, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'AI-utility' at cosine 0.798, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'ai-utility' at cosine 0.673, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'ai-utility' at cosine 0.747, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'ubiquity' at cosine 0.737, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'utility' at cosine 0.741, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'utility' at cosine 0.745, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'utility' at cosine 0.758, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'utility' at cosine 0.765, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'utility' at cosine 0.796, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | accessibility-assistance_for_disabled | Routes JUDGE against 'AI-assistance_for_disabled' at cosine 0.713, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | accessibility-assistance_for_disabled | Routes JUDGE against 'utility-work_efficiency' at cosine 0.462, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | accessibility-free_healthcare | Routes JUDGE against 'AI-economic_efficiency' at cosine 0.601, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-dependence-lifestyle | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.588, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-dependence-lifestyle | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.649, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-dependence-lifestyle | Routes JUDGE against 'ai-dependence-lifestyle' at cosine 0.722, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-dependence-lifestyle | Routes JUDGE against 'ai-dependence-lifestyle' at cosine 0.740, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-dependence-lifestyle | Routes JUDGE against 'ai-dependence-lifestyle' at cosine 0.770, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | ai-dependence-lifestyle | Routes JUDGE against 'ai-dependence-lifestyle' at cosine 0.773, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-dependence-lifestyle | Routes JUDGE against 'concern-human_dependency' at cosine 0.748, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-dependence-lifestyle | Routes JUDGE against 'dependence-lifestyle' at cosine 0.765, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-multi_use | Routes JUDGE against 'multi_use' at cosine 0.778, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-productivity_enhancement | Routes JUDGE against 'ai-productivity_enhancement' at cosine 0.692, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-productivity_enhancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.790, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-sector-focus-health | Routes JUDGE against 'AI-sector-focus-health' at cosine 0.779, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-unclear_outputs | Routes JUDGE against 'ai-unclear_outputs' at cosine 0.787, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-unclear_outputs | Routes JUDGE against 'concern-deepfakes' at cosine 0.506, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-utility | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.722, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-utility | Routes JUDGE against 'ai-productivity_enhancement' at cosine 0.661, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-utility | Routes JUDGE against 'ai-utility' at cosine 0.688, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | ai-utility | Routes JUDGE against 'utility' at cosine 0.691, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-utility | Routes JUDGE against 'utility-work_efficiency' at cosine 0.660, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | automation_of_repetitive_tasks | Routes JUDGE against 'AI-impact-immigration' at cosine 0.551, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | automation_of_repetitive_tasks | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.661, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | automation_of_repetitive_tasks | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.715, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | automation_of_repetitive_tasks-time_saving | Routes JUDGE against 'AI-automation_of_repetitive_tasks' at cosine 0.700, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | benefit-reduced_stress | Routes JUDGE against 'benefit-reduced_stress' at cosine 0.658, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | benefit-reduced_stress | Routes JUDGE against 'benefit-reduced_stress' at cosine 0.704, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | benefit-reduced_stress | Routes JUDGE against 'safety-reduced_accidents' at cosine 0.533, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | benefit-reduced_stress | Routes JUDGE against 'utility-work_ease' at cosine 0.745, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving | Routes JUDGE against 'AI-complex_problem_solving' at cosine 0.611, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving | Routes JUDGE against 'AI-complex_problem_solving' at cosine 0.716, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving | Routes JUDGE against 'AI-complex_problem_solving' at cosine 0.736, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving | Routes JUDGE against 'AI-complex_problem_solving' at cosine 0.744, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving | Routes JUDGE against 'AI-complex_problem_solving' at cosine 0.761, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving | Routes JUDGE against 'AI-complex_problem_solving' at cosine 0.791, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving | Routes JUDGE against 'AI-multi-use' at cosine 0.695, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving | Routes JUDGE against 'complex_problem_solving-advance_analysis' at cosine 0.689, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving | Routes JUDGE against 'complex_problem_solving-advance_analysis' at cosine 0.733, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving | Routes JUDGE against 'complex_problem_solving-advance_analysis' at cosine 0.753, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving | Routes JUDGE against 'complex_problem_solving-advance_analysis' at cosine 0.776, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving-advance_analysis | Routes JUDGE against 'complex_problem_solving' at cosine 0.686, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving-advance_analysis | Routes JUDGE against 'complex_problem_solving-advance_analysis' at cosine 0.649, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving-advance_analysis | Routes JUDGE against 'complex_problem_solving-advance_analysis' at cosine 0.670, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving-advance_analysis | Routes JUDGE against 'complex_problem_solving-advance_analysis' at cosine 0.739, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving-scientific_discovery | Routes JUDGE against 'complex_problem_solving' at cosine 0.641, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving-scientific_discovery | Routes JUDGE against 'complex_problem_solving' at cosine 0.788, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving-scientific_discovery | Routes JUDGE against 'complex_problem_solving-scientific_discovery' at cosine 0.764, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-deepfakes | Routes JUDGE against 'concern-deepfakes' at cosine 0.713, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | concern-deepfakes | Routes JUDGE against 'concern-human_dependency' at cosine 0.675, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-ethical_development | Routes JUDGE against 'concern-ethical_development' at cosine 0.694, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-ethical_development | Routes JUDGE against 'concern-ethical_development' at cosine 0.700, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | concern-ethical_development | Routes JUDGE against 'concern-ethical_development' at cosine 0.709, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | concern-ethical_development | Routes JUDGE against 'concern-ethical_development' at cosine 0.748, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | concern-ethical_development | Routes JUDGE against 'concern-ethical_development' at cosine 0.768, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-ethical_development | Routes JUDGE against 'concern-privacy_security' at cosine 0.724, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-human_dependency | Routes JUDGE against 'concern-human_dependency' at cosine 0.622, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-human_dependency | Routes JUDGE against 'concern-human_dependency' at cosine 0.694, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-human_dependency | Routes JUDGE against 'concern-human_dependency' at cosine 0.755, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-human_dependency | Routes JUDGE against 'concern-human_dependency' at cosine 0.794, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-human_dependency | Routes JUDGE against 'concern-privacy_security' at cosine 0.568, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-human_dependency | Routes JUDGE against 'dependence-lifestyle' at cosine 0.710, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-privacy_security | Routes JUDGE against 'AI-sector-focus-cyber_security' at cosine 0.774, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-privacy_security | Routes JUDGE against 'concern-deepfakes' at cosine 0.733, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-privacy_security | Routes JUDGE against 'concern-ethical_development' at cosine 0.743, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-privacy_security | Routes JUDGE against 'concern-ethical_development' at cosine 0.764, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-privacy_security | Routes JUDGE against 'concern-privacy_security' at cosine 0.797, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-privacy_security | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.548, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-privacy_security | Routes JUDGE against 'privacy_security' at cosine 0.723, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-privacy_security | Routes JUDGE against 'privacy_security' at cosine 0.789, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | creative_capability | Routes JUDGE against 'AI-creative_capability' at cosine 0.674, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | creative_capability | Routes JUDGE against 'AI-creative_capability' at cosine 0.717, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | creative_capability | Routes JUDGE against 'AI-creative_capability' at cosine 0.731, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | creative_capability | Routes JUDGE against 'AI-creative_capability' at cosine 0.760, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | creative_capability | Routes JUDGE against 'creative_capability' at cosine 0.748, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | creative_capability-media_generation | Routes JUDGE against 'AI-creative_capability' at cosine 0.640, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | creative_capability-media_generation | Routes JUDGE against 'creative_capability-media_generation' at cosine 0.754, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance | *message withheld: shares wording with a response* | 1 |
| M2 | WARN | route_judge | daily_life_assistance | Routes JUDGE against 'AI-daily_life_assistance' at cosine 0.694, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance | Routes JUDGE against 'AI-daily_life_assistance' at cosine 0.709, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance | Routes JUDGE against 'AI-daily_life_assistance' at cosine 0.774, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance | Routes JUDGE against 'AI-daily_life_assistance' at cosine 0.788, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.721, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance | Routes JUDGE against 'ai-utility' at cosine 0.695, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance | Routes JUDGE against 'daily_life_assistance' at cosine 0.736, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance | Routes JUDGE against 'daily_life_assistance-automated_payments' at cosine 0.713, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance | Routes JUDGE against 'utility' at cosine 0.759, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance | Routes JUDGE against 'utility' at cosine 0.773, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance | Routes JUDGE against 'utility-work_ease' at cosine 0.709, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance-automated_payments | Routes JUDGE against 'AI-automation_of_repetitive_tasks' at cosine 0.568, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance-automated_reminders | Routes JUDGE against 'daily_life_assistance-automated_payments' at cosine 0.683, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance-problem_resolution | Routes JUDGE against 'daily_life_assistance' at cosine 0.785, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance-problem_resolution | Routes JUDGE against 'daily_life_assistance-problem_resolution' at cosine 0.779, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | deepfakes | Routes JUDGE against 'concern-deepfakes' at cosine 0.713, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | deepfakes | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.639, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | dependence-lifestyle | Routes JUDGE against 'utility' at cosine 0.702, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency | Routes JUDGE against 'AI-economic_efficiency' at cosine 0.726, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | economic_efficiency | Routes JUDGE against 'AI-economic_efficiency' at cosine 0.727, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency | Routes JUDGE against 'AI-entrepreneurial-support' at cosine 0.722, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency | Routes JUDGE against 'AI-entrepreneurial-support' at cosine 0.732, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.592, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.595, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.617, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.677, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.685, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.704, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.754, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.682, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency | Routes JUDGE against 'economic_efficiency-productivity_gain' at cosine 0.708, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency-productivity_gain | Routes JUDGE against 'AI-economic_efficiency' at cosine 0.678, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency-productivity_gain | Routes JUDGE against 'economic_efficiency-productivity_gain' at cosine 0.788, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | economic_efficiency-productivity_gain | Routes JUDGE against 'economic_impact-productivity_gain' at cosine 0.659, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency-recession | Routes JUDGE against 'economic_efficiency' at cosine 0.657, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_impact-productivity_gain | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.618, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_impact-productivity_gain | Routes JUDGE against 'economic_impact-productivity_gain' at cosine 0.691, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_impact-universal_basic_income | Routes JUDGE against 'impact-technological_advancement' at cosine 0.507, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | education-accessibility | Routes JUDGE against 'education' at cosine 0.613, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | education-literacy_requirement | Routes JUDGE against 'AI-need_for_awareness' at cosine 0.622, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | education-personalised_learning | *message withheld: shares wording with a response* | 1 |
| M2 | WARN | route_judge | education-sector-transformation | Routes JUDGE against 'education-sector-transformation' at cosine 0.790, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | education-sector-transformation | Routes JUDGE against 'sector-focus-cyber_security' at cosine 0.685, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | education-sector-transformation | Routes JUDGE against 'sector-focus-education' at cosine 0.767, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | education-sector_transformation | Routes JUDGE against 'education-sector-transformation' at cosine 0.733, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.720, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation | Routes JUDGE against 'creative_capability' at cosine 0.682, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation | Routes JUDGE against 'employment_transformation' at cosine 0.578, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation | Routes JUDGE against 'employment_transformation-job_displacement' at cosine 0.740, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation | Routes JUDGE against 'employment_transformation-job_displacement' at cosine 0.772, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation | Routes JUDGE against 'sector_transformation' at cosine 0.662, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation | Routes JUDGE against 'sector_transformation' at cosine 0.665, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation | Routes JUDGE against 'sector_transformation' at cosine 0.717, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-job_creation | Routes JUDGE against 'AI-employment_transformation' at cosine 0.698, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-job_creation | Routes JUDGE against 'AI-employment_transformation' at cosine 0.780, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | employment_transformation-job_creation | Routes JUDGE against 'employment_transformation' at cosine 0.738, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-job_creation | Routes JUDGE against 'employment_transformation-job_creation' at cosine 0.792, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-job_creation | Routes JUDGE against 'employment_transformation-job_displacement' at cosine 0.701, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-job_displacement | Routes JUDGE against 'AI-employment_transformation' at cosine 0.765, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-job_displacement | Routes JUDGE against 'employment_transformation' at cosine 0.720, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-job_displacement | Routes JUDGE against 'employment_transformation-job_displacement' at cosine 0.661, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-job_displacement | Routes JUDGE against 'employment_transformation-job_displacement' at cosine 0.719, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-job_displacement | Routes JUDGE against 'employment_transformation-job_displacement' at cosine 0.754, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-job_displacement | Routes JUDGE against 'employment_transformation-job_displacement' at cosine 0.763, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | employment_transformation-job_displacement | Routes JUDGE against 'employment_transformation-job_displacement' at cosine 0.795, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 2 |
| M2 | WARN | route_judge | employment_transformation-job_displacement | Routes JUDGE against 'sector_transformation' at cosine 0.690, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-job_transformation | Routes JUDGE against 'sector_transformation' at cosine 0.755, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-remote_work | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.564, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-workforce_retraining | Routes JUDGE against 'AI-employment_transformation' at cosine 0.714, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | employment_transformation-workforce_retraining | Routes JUDGE against 'education-sector-transformation' at cosine 0.623, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-workforce_retraining | Routes JUDGE against 'employment_transformation-job_displacement' at cosine 0.709, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-workforce_retraining | Routes JUDGE against 'employment_transformation-workforce_retraining' at cosine 0.691, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-workforce_retraining | Routes JUDGE against 'employment_transformation-workforce_retraining' at cosine 0.731, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-workforce_retraining | Routes JUDGE against 'employment_transformation-workforce_retraining' at cosine 0.743, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-workforce_retraining | Routes JUDGE against 'employment_transformation-workforce_retraining' at cosine 0.767, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation-workforce_retraining | Routes JUDGE against 'mindset_shift' at cosine 0.723, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | enhanced-communication | Routes JUDGE against 'impact-enhanced-communication' at cosine 0.753, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | facilitated-collaboration | Routes JUDGE against 'utility-work_ease' at cosine 0.722, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | global_defence | Routes JUDGE against 'AI-global_defence' at cosine 0.700, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | global_defence | Routes JUDGE against 'sector-focus-cyber_security' at cosine 0.650, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-communication_enhancement | Routes JUDGE against 'AI-enhanced-communication' at cosine 0.605, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-communication_enhancement | Routes JUDGE against 'AI-enhanced-communication' at cosine 0.759, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-communication_enhancement | Routes JUDGE against 'AI-impact-women_safety' at cosine 0.494, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-communication_enhancement | Routes JUDGE against 'society-digital-transformation' at cosine 0.628, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-digital_connectivity | Routes JUDGE against 'AI-enhanced-communication' at cosine 0.751, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-digital_exclusion | Routes JUDGE against 'impact-digital_exclusion' at cosine 0.615, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-digital_exclusion | Routes JUDGE against 'impact-digital_exclusion' at cosine 0.789, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-digital_exclusion | Routes JUDGE against 'labor-job_transformation' at cosine 0.652, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-enhanced-communication | Routes JUDGE against 'impact-communication_enhancement' at cosine 0.738, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-public_safety | Routes JUDGE against 'AI-economic_efficiency' at cosine 0.618, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-public_safety | Routes JUDGE against 'AI-impact-women_safety' at cosine 0.604, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-public_safety | Routes JUDGE against 'impact-public_safety' at cosine 0.665, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-public_safety | Routes JUDGE against 'impact-public_safety' at cosine 0.683, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-public_safety | Routes JUDGE against 'impact-public_safety' at cosine 0.762, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-public_safety | Routes JUDGE against 'impact-public_safety' at cosine 0.793, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-public_safety | Routes JUDGE against 'sector-focus-cyber_security' at cosine 0.746, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-rapid_change | Routes JUDGE against 'AI-impact-immigration' at cosine 0.741, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-rapid_change | Routes JUDGE against 'AI-impact-immigration' at cosine 0.751, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-rapid_change | Routes JUDGE against 'impact-technological_advancement' at cosine 0.664, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-rapid_change | Routes JUDGE against 'society-digital-transformation' at cosine 0.530, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-rapid_change | Routes JUDGE against 'society-digital-transformation' at cosine 0.696, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'AI-entrepreneurial-support' at cosine 0.670, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'AI-entrepreneurial-support' at cosine 0.712, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'AI-entrepreneurial-support' at cosine 0.755, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'AI-impact-rapid_change' at cosine 0.702, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.687, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.710, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'AI-robotics_engineering' at cosine 0.532, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'AI-sector-focus-transportation' at cosine 0.599, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'economic_efficiency' at cosine 0.664, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'economic_efficiency-productivity_gain' at cosine 0.718, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'economic_impact-productivity_gain' at cosine 0.669, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-enhanced-communication' at cosine 0.762, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.586, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.589, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.617, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.630, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.655, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.669, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.674, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.677, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.692, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.697, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.704, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.710, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.715, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.729, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.733, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.742, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.762, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.770, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.620, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'positive_outlook' at cosine 0.726, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'safety-reduced_accidents' at cosine 0.578, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'ubiquity' at cosine 0.656, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'ubiquity' at cosine 0.717, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-work_ease | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.581, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-work_ease | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.775, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-work_ease | Routes JUDGE against 'impact-work_ease' at cosine 0.591, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-work_ease | Routes JUDGE against 'impact-work_ease' at cosine 0.758, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-work_ease | Routes JUDGE against 'impact-work_ease' at cosine 0.758, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | impact-work_ease | Routes JUDGE against 'impact-work_ease' at cosine 0.771, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-work_ease | Routes JUDGE against 'impact-work_ease' at cosine 0.779, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | impact-work_ease | Routes JUDGE against 'utility-work_ease' at cosine 0.706, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | job_displacement | Routes JUDGE against 'employment_transformation-job_displacement' at cosine 0.747, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | labor-competitive_advantage | Routes JUDGE against 'benefit-reduced_stress' at cosine 0.549, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | labor-competitive_advantage | Routes JUDGE against 'labor-competitive_advantage' at cosine 0.643, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | labor-competitive_advantage | Routes JUDGE against 'labor-competitive_advantage' at cosine 0.729, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | labor-free_workforce | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.679, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | labor-job_transformation | Routes JUDGE against 'impact-public_safety' at cosine 0.585, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | labor-job_transformation | Routes JUDGE against 'labor-job_transformation' at cosine 0.601, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | labor-job_transformation | Routes JUDGE against 'labor-job_transformation' at cosine 0.759, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | mindset_shift | Routes JUDGE against 'AI-mindset_shift' at cosine 0.774, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | mindset_shift | Routes JUDGE against 'creative_capability' at cosine 0.773, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | mindset_shift | Routes JUDGE against 'positive_outlook' at cosine 0.677, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | mindset_shift-problem_identification | Routes JUDGE against 'AI-mindset_shift' at cosine 0.669, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | mindset_shift-problem_identification | Routes JUDGE against 'AI-perception-central_role' at cosine 0.704, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | multi-use | Routes JUDGE against 'AI-multi-use' at cosine 0.721, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | multi-use | Routes JUDGE against 'AI-multi-use' at cosine 0.741, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | multi-use | Routes JUDGE against 'AI-multi-use' at cosine 0.793, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | multi-use | Routes JUDGE against 'AI-multi-use' at cosine 0.797, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | multi-use | Routes JUDGE against 'multi-use' at cosine 0.669, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | multi-use | Routes JUDGE against 'multi-use' at cosine 0.696, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | multi-use | Routes JUDGE against 'multi-use' at cosine 0.762, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | multi-use | Routes JUDGE against 'multi-use' at cosine 0.763, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | multi-use | Routes JUDGE against 'multi-use' at cosine 0.770, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | multi_use | Routes JUDGE against 'AI-multi-use' at cosine 0.671, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | multi_use | Routes JUDGE against 'multi-use' at cosine 0.750, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness | Routes JUDGE against 'AI-need_for_awareness' at cosine 0.644, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness | Routes JUDGE against 'AI-need_for_awareness' at cosine 0.658, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness | Routes JUDGE against 'AI-need_for_awareness' at cosine 0.738, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness | Routes JUDGE against 'education-literacy_requirement' at cosine 0.631, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness | Routes JUDGE against 'employment_transformation-workforce_retraining' at cosine 0.698, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness | Routes JUDGE against 'need_for_awareness' at cosine 0.548, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness | Routes JUDGE against 'need_for_awareness' at cosine 0.608, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness | Routes JUDGE against 'need_for_awareness' at cosine 0.656, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | need_for_awareness | Routes JUDGE against 'need_for_awareness' at cosine 0.691, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness | Routes JUDGE against 'need_for_awareness' at cosine 0.748, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness | Routes JUDGE against 'need_for_awareness' at cosine 0.758, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | need_for_awareness | Routes JUDGE against 'negative_impacts-cybersecurity_risks' at cosine 0.604, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness | Routes JUDGE against 'threat-to-humanity' at cosine 0.646, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness-literacy | Routes JUDGE against 'education-literacy_requirement' at cosine 0.695, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness-literacy | Routes JUDGE against 'education-literacy_requirement' at cosine 0.708, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness-literacy | Routes JUDGE against 'education-literacy_requirement' at cosine 0.741, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness-literacy | Routes JUDGE against 'need_for_awareness-literacy' at cosine 0.752, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | need_for_awareness-literacy | Routes JUDGE against 'ubiquity' at cosine 0.708, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.701, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.767, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-cybersecurity_risks | Routes JUDGE against 'AI-sector-focus-cyber_security' at cosine 0.562, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-dual_nature | Routes JUDGE against 'AI-positive_outlook' at cosine 0.616, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-dual_nature | Routes JUDGE against 'negative_impacts-dual_nature' at cosine 0.745, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | negative_impacts-dual_nature | Routes JUDGE against 'negative_impacts-dual_nature' at cosine 0.794, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | negative_impacts-human_subjugation | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.768, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-human_subjugation | Routes JUDGE against 'concern-human_dependency' at cosine 0.796, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-human_subjugation | Routes JUDGE against 'negative_impacts-human_subjugation' at cosine 0.776, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.723, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.763, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'concern-human_dependency' at cosine 0.679, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'concern-human_dependency' at cosine 0.717, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'concern-human_dependency' at cosine 0.728, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'employment_transformation-job_displacement' at cosine 0.684, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'employment_transformation-job_displacement' at cosine 0.790, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'job_displacement' at cosine 0.695, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'job_displacement' at cosine 0.698, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'job_displacement' at cosine 0.728, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'job_displacement' at cosine 0.741, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'job_displacement' at cosine 0.757, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'job_displacement' at cosine 0.767, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'job_displacement' at cosine 0.791, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'job_displacement' at cosine 0.796, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-human_subjugation' at cosine 0.797, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-job_destruction' at cosine 0.703, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-job_destruction' at cosine 0.727, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-job_destruction' at cosine 0.735, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-job_destruction' at cosine 0.755, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 2 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-job_destruction' at cosine 0.758, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-job_destruction' at cosine 0.759, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-job_destruction' at cosine 0.764, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-job_destruction' at cosine 0.778, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-job_destruction' at cosine 0.779, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-job_destruction' at cosine 0.787, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.612, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.629, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.692, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.734, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-laziness | Routes JUDGE against 'concern-human_dependency' at cosine 0.744, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-laziness | Routes JUDGE against 'concern-human_dependency' at cosine 0.748, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-laziness | Routes JUDGE against 'concern-human_dependency' at cosine 0.752, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-laziness | Routes JUDGE against 'labor-free_workforce' at cosine 0.698, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-laziness | Routes JUDGE against 'negative_impacts-laziness' at cosine 0.761, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-laziness | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.538, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-laziness | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.764, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-laziness | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.794, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-laziness | Routes JUDGE against 'negative_impacts-physical_health' at cosine 0.769, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'AI-positive_outlook' at cosine 0.730, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'concern-ethical_development' at cosine 0.703, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.635, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.700, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.709, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.721, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.743, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.745, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.750, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.751, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.754, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.779, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.795, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'negative_impacts-physical_health' at cosine 0.776, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-physical_health | Routes JUDGE against 'negative_impacts-human_subjugation' at cosine 0.700, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-physical_health | Routes JUDGE against 'negative_impacts-laziness' at cosine 0.608, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | perception-central_role | Routes JUDGE against 'AI-perception-central_role' at cosine 0.726, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | perception-central_role | Routes JUDGE against 'AI-perception-central_role' at cosine 0.749, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | perception-central_role | Routes JUDGE against 'AI-perception-central_role' at cosine 0.751, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | perception-central_role | Routes JUDGE against 'AI-perception-central_role' at cosine 0.764, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | perception-central_role | Routes JUDGE against 'AI-perception-central_role' at cosine 0.766, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | perception-central_role | Routes JUDGE against 'AI-perception-central_role' at cosine 0.778, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | perception-central_role | Routes JUDGE against 'AI-superintelligence' at cosine 0.632, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | perception-fleeting_trend | Routes JUDGE against 'perception-technological_luck' at cosine 0.535, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | perception-technological_luck | Routes JUDGE against 'AI-positive_outlook' at cosine 0.512, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outcomes-accessible_healthcare | Routes JUDGE against 'sector-focus-health' at cosine 0.725, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outcomes-work_relief | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.638, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outcomes-work_relief | Routes JUDGE against 'positive_outcomes-work_relief' at cosine 0.679, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outcomes-work_relief | Routes JUDGE against 'positive_outcomes-work_relief' at cosine 0.708, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | positive_outcomes-work_relief | Routes JUDGE against 'positive_outcomes-work_relief' at cosine 0.722, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | positive_outcomes-work_relief | Routes JUDGE against 'positive_outcomes-work_relief' at cosine 0.739, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | positive_outcomes-work_relief | Routes JUDGE against 'positive_outcomes-work_relief' at cosine 0.760, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | positive_outcomes-work_relief | Routes JUDGE against 'positive_outcomes-work_relief' at cosine 0.777, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outcomes-work_relief | Routes JUDGE against 'positive_outcomes-work_relief' at cosine 0.800, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outcomes-work_relief | Routes JUDGE against 'positive_outlook-work_relief' at cosine 0.717, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'AI-enhanced-communication' at cosine 0.708, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'AI-positive_outlook' at cosine 0.793, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outcomes-work_relief' at cosine 0.704, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.575, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.691, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.700, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.710, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.724, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.727, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.734, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.735, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.738, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.743, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.749, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.756, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.777, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.789, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.794, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.795, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.795, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.796, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.797, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.798, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook-wealth_and_happiness | Routes JUDGE against 'AI-positive_outlook' at cosine 0.698, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook-wealth_and_happiness | Routes JUDGE against 'positive_outlook' at cosine 0.737, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook-wealth_and_happiness | Routes JUDGE against 'positive_outlook' at cosine 0.785, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook-wealth_and_happiness | Routes JUDGE against 'positive_outlook-wealth_and_happiness' at cosine 0.659, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | positive_outlook-wealth_and_happiness | Routes JUDGE against 'positive_outlook-wealth_and_happiness' at cosine 0.734, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | positive_outlook-wealth_and_happiness | Routes JUDGE against 'positive_outlook-wealth_and_happiness' at cosine 0.787, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | positive_outlook-wealth_and_happiness | Routes JUDGE against 'positive_outlook-wealth_and_happiness' at cosine 0.794, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | positive_outlook-work_relief | Routes JUDGE against 'positive_outcomes-work_relief' at cosine 0.649, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook-work_relief | Routes JUDGE against 'positive_outcomes-work_relief' at cosine 0.799, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | positive_outlook-work_relief | Routes JUDGE against 'positive_outlook' at cosine 0.779, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook-work_relief | Routes JUDGE against 'positive_outlook-work_relief' at cosine 0.736, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | privacy_security | Routes JUDGE against 'concern-privacy_security' at cosine 0.733, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | privacy_security-safe_sharing | Routes JUDGE against 'concern-ethical_development' at cosine 0.594, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | privacy_security-safe_sharing | Routes JUDGE against 'privacy_security-safe_sharing' at cosine 0.613, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | robotics_engineering | Routes JUDGE against 'AI-robotics_engineering' at cosine 0.542, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | robotics_engineering | Routes JUDGE against 'facilitated-collaboration' at cosine 0.596, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | role_human_replacement | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.565, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | safety-human_safety | Routes JUDGE against 'safety-kill_switch' at cosine 0.714, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | safety-improvements-shelter_security | Routes JUDGE against 'AI-impact-women_safety' at cosine 0.706, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | safety-improvements-shelter_security | Routes JUDGE against 'safety-reduced_accidents' at cosine 0.659, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | safety-improvements-shelter_security | Routes JUDGE against 'safety_improvements' at cosine 0.625, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | safety-kill_switch | Routes JUDGE against 'concern-ethical_development' at cosine 0.491, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | safety-reduced_accidents | Routes JUDGE against 'AI-impact-women_safety' at cosine 0.571, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | safety-reduced_accidents | Routes JUDGE against 'safety-reduced_accidents' at cosine 0.667, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | safety-reduced_accidents | Routes JUDGE against 'safety-reduced_accidents' at cosine 0.695, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | safety_improvements | Routes JUDGE against 'safety-reduced_accidents' at cosine 0.560, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-cyber_security | Routes JUDGE against 'AI-sector-focus-cyber_security' at cosine 0.707, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-cyber_security | Routes JUDGE against 'sector-focus-cyber_security' at cosine 0.700, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-cyber_security | Routes JUDGE against 'sector-focus-cyber_security' at cosine 0.781, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-digital_marketing | Routes JUDGE against 'AI-sector-focus-defence_education' at cosine 0.746, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-digital_marketing | Routes JUDGE against 'sector-focus-digital_marketing' at cosine 0.736, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-digital_marketing | Routes JUDGE against 'sector-focus-digital_marketing' at cosine 0.750, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | sector-focus-digital_marketing | Routes JUDGE against 'sector-focus-digital_marketing' at cosine 0.753, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | sector-focus-digital_marketing | Routes JUDGE against 'sector-focus-digital_marketing' at cosine 0.759, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-education | Routes JUDGE against 'sector-focus-health' at cosine 0.724, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-education | Routes JUDGE against 'sector-focus-transportation' at cosine 0.682, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-health | Routes JUDGE against 'AI-assistance_for_disabled' at cosine 0.784, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-health | Routes JUDGE against 'AI-sector-focus-health' at cosine 0.785, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-health | Routes JUDGE against 'AI-sector-focus-health' at cosine 0.798, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-health | Routes JUDGE against 'sector-focus-health' at cosine 0.506, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-health | Routes JUDGE against 'sector-focus-health' at cosine 0.734, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-health | Routes JUDGE against 'sector-focus-health' at cosine 0.781, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-health | Routes JUDGE against 'sector-focus-hospitality' at cosine 0.717, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-health | Routes JUDGE against 'sector-focus-hospitality' at cosine 0.755, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-hospitality | Routes JUDGE against 'sector-focus-transportation' at cosine 0.624, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-programming | Routes JUDGE against 'sector-focus-digital_marketing' at cosine 0.736, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-programming | Routes JUDGE against 'sector-focus-programming' at cosine 0.748, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-real_estate | Routes JUDGE against 'sector-focus-digital_marketing' at cosine 0.717, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-transportation | Routes JUDGE against 'AI-sector_transformation' at cosine 0.706, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-transportation | Routes JUDGE against 'sector-focus-transportation' at cosine 0.792, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector_transformation | Routes JUDGE against 'AI-sector_transformation' at cosine 0.722, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector_transformation | Routes JUDGE against 'labor-job_transformation' at cosine 0.651, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | society-digital-transformation | Routes JUDGE against 'AI-impact-women_safety' at cosine 0.512, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | society-digital-transformation | Routes JUDGE against 'society-digital-transformation' at cosine 0.614, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | society-digital-transformation | Routes JUDGE against 'society-digital-transformation' at cosine 0.673, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | society-digital-transformation | Routes JUDGE against 'society-digital-transformation' at cosine 0.689, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | society-digital-transformation | Routes JUDGE against 'society-digital-transformation' at cosine 0.782, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | society-social_norms | Routes JUDGE against 'AI-enhanced-communication' at cosine 0.664, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | society-social_norms | Routes JUDGE against 'AI-enhanced-communication' at cosine 0.686, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | society-social_norms | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.608, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | society-social_norms | Routes JUDGE against 'positive_outlook' at cosine 0.699, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | threat-to-humanity | Routes JUDGE against 'negative_impacts-human_subjugation' at cosine 0.741, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | threat-to-humanity | Routes JUDGE against 'threat-to-humanity' at cosine 0.632, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | threat-to-humanity | Routes JUDGE against 'threat-to-humanity' at cosine 0.777, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | threat-to-humanity | Routes JUDGE against 'threat-to-humanity' at cosine 0.782, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | threat-to-humanity | Routes JUDGE against 'threat-to-humanity' at cosine 0.797, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transport_automation | Routes JUDGE against 'transportation-autonomous_vehicles' at cosine 0.594, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.508, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.696, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'AI-sector-focus-transportation' at cosine 0.699, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'AI-sector-focus-transportation' at cosine 0.761, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'AI-transportation-autonomous_vehicles' at cosine 0.704, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 2 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'AI-transportation-autonomous_vehicles' at cosine 0.793, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'sector-focus-cyber_security' at cosine 0.597, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'sector-focus-cyber_security' at cosine 0.684, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'sector-focus-transportation' at cosine 0.685, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'transport_automation' at cosine 0.741, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'transportation-autonomous_vehicles' at cosine 0.635, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'transportation-autonomous_vehicles' at cosine 0.647, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'transportation-navigation_assistance' at cosine 0.722, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-navigation_assistance | Routes JUDGE against 'accessibility-assistance_for_disabled' at cosine 0.649, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-navigation_assistance | Routes JUDGE against 'transportation-navigation_assistance' at cosine 0.739, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'AI-multi-use' at cosine 0.757, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'AI-role_human_replacement' at cosine 0.689, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.609, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.681, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.744, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.770, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.777, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.792, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'ubiquity' at cosine 0.693, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'ubiquity' at cosine 0.730, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'ubiquity' at cosine 0.733, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'ubiquity' at cosine 0.734, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 2 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'ubiquity' at cosine 0.745, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'ubiquity' at cosine 0.753, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'ubiquity' at cosine 0.758, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'ubiquity' at cosine 0.760, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'ubiquity' at cosine 0.771, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'ubiquity' at cosine 0.780, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | unclear_outputs | Routes JUDGE against 'ai-unclear_outputs' at cosine 0.715, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | unclear_outputs | Routes JUDGE against 'unclear_outputs' at cosine 0.660, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | user_experience_relaxation | Routes JUDGE against 'user_experience_relaxation' at cosine 0.670, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | user_experience_relaxation | Routes JUDGE against 'utility-work_efficiency' at cosine 0.460, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | utility | Routes JUDGE against 'AI-utility' at cosine 0.776, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | utility | Routes JUDGE against 'ai-utility' at cosine 0.745, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | utility | Routes JUDGE against 'ubiquity' at cosine 0.790, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | utility | Routes JUDGE against 'utility' at cosine 0.787, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | utility-efficiency_gain | Routes JUDGE against 'utility-work_efficiency' at cosine 0.769, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | utility-work_ease | Routes JUDGE against 'utility' at cosine 0.780, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | utility-work_ease | Routes JUDGE against 'utility-work_ease' at cosine 0.639, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | utility-work_ease | Routes JUDGE against 'utility-work_ease' at cosine 0.678, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | utility-work_ease | Routes JUDGE against 'utility-work_ease' at cosine 0.773, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | utility-work_ease | Routes JUDGE against 'utility-work_ease' at cosine 0.783, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | utility-work_ease | Routes JUDGE against 'utility-work_ease' at cosine 0.800, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 2 |
| M2 | WARN | route_judge | utility-work_efficiency | Routes JUDGE against 'AI-economic_efficiency' at cosine 0.709, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | utility-work_efficiency | Routes JUDGE against 'ai-utility' at cosine 0.685, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | utility-work_efficiency | Routes JUDGE against 'ai-utility' at cosine 0.719, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | utility-work_efficiency | Routes JUDGE against 'economic_impact-productivity_gain' at cosine 0.676, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | utility-work_efficiency | Routes JUDGE against 'impact-work_ease' at cosine 0.775, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | utility-work_efficiency | Routes JUDGE against 'utility-work_ease' at cosine 0.681, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | utility-work_efficiency | Routes JUDGE against 'utility-work_efficiency' at cosine 0.770, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | utility-work_efficiency | Routes JUDGE against 'utility-work_efficiency' at cosine 0.775, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | workforce_retraining | Routes JUDGE against 'employment_transformation-workforce_retraining' at cosine 0.697, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M3 | ERROR | candidate_dropped_no_evidence | AI-multi_use | Candidate 'AI-multi_use' is dropped: every verified quote was ruled UNNECESSARY, so nothing in the corpus supports it any longer. | 1 |
| M3 | ERROR | candidate_dropped_no_evidence | ai-dependence-lifestyle | Candidate 'ai-dependence-lifestyle' is dropped: every verified quote was ruled UNNECESSARY, so nothing in the corpus supports it any longer. | 1 |
| M3 | ERROR | candidate_dropped_no_evidence | benefit-reduced_stress | Candidate 'benefit-reduced_stress' is dropped: every verified quote was ruled UNNECESSARY, so nothing in the corpus supports it any longer. | 1 |
| M3 | ERROR | candidate_dropped_no_evidence | impact-public_safety | Candidate 'impact-public_safety' is dropped: every verified quote was ruled UNNECESSARY, so nothing in the corpus supports it any longer. | 1 |
| M3 | ERROR | candidate_dropped_no_evidence | negative_impacts-human_subjugation | Candidate 'negative_impacts-human_subjugation' is dropped: every verified quote was ruled UNNECESSARY, so nothing in the corpus supports it any longer. | 1 |
| M3 | ERROR | candidate_dropped_no_evidence | sector-focus-digital_marketing | Candidate 'sector-focus-digital_marketing' is dropped: every verified quote was ruled UNNECESSARY, so nothing in the corpus supports it any longer. | 1 |
| M3 | WARN | fit_imprecise | impact-technological_advancement | Judge ruled IMPRECISE on 'impact-technological_advancement' in response 167 (fit 0.280 < tau_fit 0.30): the code was not precise enough for this quote; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | *message withheld: shares wording with a response* | *message withheld: shares wording with a response* | 1 |
| M3 | WARN | fit_incomplete | *message withheld: shares wording with a response* | Judge ruled INCOMPLETE on 'education' in response 509 (fit 0.286 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | AI-automation_of_repetitive_tasks | Judge ruled INCOMPLETE on 'AI-automation_of_repetitive_tasks' in response 81 (fit 0.253 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | AI-role-human_replacement | Judge ruled INCOMPLETE on 'AI-role-human_replacement' in response 383 (fit 0.279 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | AI-utility | Judge ruled INCOMPLETE on 'AI-utility' in response 565 (fit 0.289 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | concern-human_dependency | Judge ruled INCOMPLETE on 'concern-human_dependency' in response 235 (fit 0.266 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | concern-human_dependency | Judge ruled INCOMPLETE on 'concern-human_dependency' in response 522 (fit 0.268 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | daily_life_assistance | Judge ruled INCOMPLETE on 'daily_life_assistance' in response 395 (fit 0.259 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | economic_impact | Judge ruled INCOMPLETE on 'economic_impact' in response 94 (fit 0.262 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | education-sector_transformation | Judge ruled INCOMPLETE on 'education-sector_transformation' in response 234 (fit 0.168 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | impact-technological_advancement | Judge ruled INCOMPLETE on 'impact-technological_advancement' in response 77 (fit 0.294 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | multi-use | Judge ruled INCOMPLETE on 'multi-use' in response 427 (fit 0.254 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | negative_impacts-human_subjugation | Judge ruled INCOMPLETE on 'negative_impacts-human_subjugation' in response 395 (fit 0.227 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | positive_outcomes-work_relief | Judge ruled INCOMPLETE on 'positive_outcomes-work_relief' in response 262 (fit 0.279 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | positive_outcomes-work_relief | Judge ruled INCOMPLETE on 'positive_outcomes-work_relief' in response 565 (fit 0.242 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | positive_outlook | Judge ruled INCOMPLETE on 'positive_outlook' in response 278 (fit 0.260 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | positive_outlook | Judge ruled INCOMPLETE on 'positive_outlook' in response 503 (fit 0.289 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | positive_outlook | Judge ruled INCOMPLETE on 'positive_outlook' in response 52 (fit 0.289 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | positive_outlook | Judge ruled INCOMPLETE on 'positive_outlook' in response 94 (fit 0.289 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | productivity_enhancement | Judge ruled INCOMPLETE on 'productivity_enhancement' in response 215 (fit 0.292 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | ubiquity | Judge ruled INCOMPLETE on 'ubiquity' in response 324 (fit 0.233 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | utility | Judge ruled INCOMPLETE on 'utility' in response 509 (fit 0.189 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | quote_removed_unnecessary | AI-multi_use | Judge ruled UNNECESSARY on 'AI-multi_use' in response 517 (fit 0.252 < tau_fit 0.30): the code did not have to be applied here, so the quote is removed from this candidate's evidence. | 1 |
| M3 | WARN | quote_removed_unnecessary | ai-dependence-lifestyle | Judge ruled UNNECESSARY on 'ai-dependence-lifestyle' in response 203 (fit 0.185 < tau_fit 0.30): the code did not have to be applied here, so the quote is removed from this candidate's evidence. | 1 |
| M3 | WARN | quote_removed_unnecessary | benefit-reduced_stress | Judge ruled UNNECESSARY on 'benefit-reduced_stress' in response 278 (fit 0.275 < tau_fit 0.30): the code did not have to be applied here, so the quote is removed from this candidate's evidence. | 1 |
| M3 | WARN | quote_removed_unnecessary | impact-public_safety | Judge ruled UNNECESSARY on 'impact-public_safety' in response 474 (fit 0.286 < tau_fit 0.30): the code did not have to be applied here, so the quote is removed from this candidate's evidence. | 1 |
| M3 | WARN | quote_removed_unnecessary | negative_impacts-human_subjugation | Judge ruled UNNECESSARY on 'negative_impacts-human_subjugation' in response 522 (fit 0.229 < tau_fit 0.30): the code did not have to be applied here, so the quote is removed from this candidate's evidence. | 1 |
| M3 | WARN | quote_removed_unnecessary | sector-focus-digital_marketing | Judge ruled UNNECESSARY on 'sector-focus-digital_marketing' in response 458 (fit 0.270 < tau_fit 0.30): the code did not have to be applied here, so the quote is removed from this candidate's evidence. | 1 |
| S1 | ERROR | missing_evidence | impact-women_safety | Candidate cites no evidence, so it cannot be traced back to the corpus. | 1 |
| S2 | ERROR | no_verified_evidence | *message withheld: shares wording with a response* | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 1 |
| S2 | ERROR | no_verified_evidence | AI-productivity_enhancement | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 1 |
| S2 | ERROR | no_verified_evidence | AI-sector-focus-transportation | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 1 |
| S2 | ERROR | no_verified_evidence | AI-ubiquity | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 3 |
| S2 | ERROR | no_verified_evidence | economic_efficiency-productivity_gain | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 1 |
| S2 | ERROR | no_verified_evidence | eliminating_biases | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 1 |
| S2 | ERROR | no_verified_evidence | multi-use | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 2 |
| S2 | ERROR | no_verified_evidence | perception-central_role | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 1 |
| S2 | ERROR | no_verified_evidence | sector-focus-transportation | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 1 |
| S2 | ERROR | no_verified_evidence | transportation-autonomous_vehicles | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 1 |
| S2 | ERROR | no_verified_evidence | ubiquity | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 1 |
| S2 | ERROR | no_verified_evidence | utility-work_ease | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 1 |
| S2b | WARN | quote_too_long | AI-positive_outlook | Quote spans 3 sentences; coding should be applied at the level of phrase or sentence (at most 2). | 1 |
| S2b | WARN | quote_too_long | AI-productivity_enhancement | Quote spans 3 sentences; coding should be applied at the level of phrase or sentence (at most 2). | 2 |
| S2b | WARN | quote_too_long | AI-sector-focus-health | Quote spans 4 sentences; coding should be applied at the level of phrase or sentence (at most 2). | 1 |
| S2b | WARN | quote_too_long | AI-utility | Quote spans 3 sentences; coding should be applied at the level of phrase or sentence (at most 2). | 1 |
| S2b | WARN | quote_too_long | automation_of_repetitive_tasks | Quote spans 3 sentences; coding should be applied at the level of phrase or sentence (at most 2). | 1 |
| S2b | WARN | quote_too_long | creative_capability | Quote spans 3 sentences; coding should be applied at the level of phrase or sentence (at most 2). | 1 |
| S2b | WARN | quote_too_long | impact-technological_advancement | Quote spans 3 sentences; coding should be applied at the level of phrase or sentence (at most 2). | 1 |
| S2b | WARN | quote_too_long | multi-use | Quote spans 3 sentences; coding should be applied at the level of phrase or sentence (at most 2). | 1 |
| S2b | WARN | quote_too_long | negative_impacts-dual_nature | Quote spans 3 sentences; coding should be applied at the level of phrase or sentence (at most 2). | 1 |
| S2b | WARN | quote_too_long | transportation-autonomous_vehicles | Quote spans 3 sentences; coding should be applied at the level of phrase or sentence (at most 2). | 1 |
| S2b | WARN | quote_too_long_words | AI-behavioral_influence | Quote runs to 43 words; coding should be applied at the level of phrase or sentence (at most 40 words). | 1 |
| S2b | WARN | quote_too_long_words | concern-human_dependency | Quote runs to 47 words; coding should be applied at the level of phrase or sentence (at most 40 words). | 1 |
| S3 | WARN | sub_code_first | *message withheld: shares wording with a response* | *message withheld: shares wording with a response* | 21 |
| S3 | WARN | sub_code_first | *message withheld: shares wording with a response* | The family 'education' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 3 |
| S3 | WARN | sub_code_first | automation_of_repetitive_tasks | The family 'automation_of_repetitive_tasks' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 5 |
| S3 | WARN | sub_code_first | complex_problem_solving | The family 'complex_problem_solving' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 19 |
| S3 | WARN | sub_code_first | creative_capability | The family 'creative_capability' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 4 |
| S3 | WARN | sub_code_first | daily_life_assistance | The family 'daily_life_assistance' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 29 |
| S3 | WARN | sub_code_first | deepfakes | The family 'deepfakes' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 1 |
| S3 | WARN | sub_code_first | economic_efficiency | The family 'economic_efficiency' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 18 |
| S3 | WARN | sub_code_first | economic_impact | The family 'economic_impact' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 1 |
| S3 | WARN | sub_code_first | employment_transformation | The family 'employment_transformation' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 18 |
| S3 | WARN | sub_code_first | global_defence | The family 'global_defence' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 1 |
| S3 | WARN | sub_code_first | job_displacement | The family 'job_displacement' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 8 |
| S3 | WARN | sub_code_first | mindset_shift | The family 'mindset_shift' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 2 |
| S3 | WARN | sub_code_first | multi_use | The family 'multi_use' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 8 |
| S3 | WARN | sub_code_first | need_for_awareness | The family 'need_for_awareness' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 14 |
| S3 | WARN | sub_code_first | negative_impacts | The family 'negative_impacts' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 2 |
| S3 | WARN | sub_code_first | positive_outcomes | The family 'positive_outcomes' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 1 |
| S3 | WARN | sub_code_first | positive_outlook | The family 'positive_outlook' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 107 |
| S3 | WARN | sub_code_first | privacy_security | The family 'privacy_security' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 2 |
| S3 | WARN | sub_code_first | robotics_engineering | The family 'robotics_engineering' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 1 |
| S3 | WARN | sub_code_first | sector_transformation | The family 'sector_transformation' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 6 |
| S3 | WARN | sub_code_first | security | The family 'security' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 1 |
| S3 | WARN | sub_code_first | ubiquity | The family 'ubiquity' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 58 |
| S3 | WARN | sub_code_first | unclear_outputs | The family 'unclear_outputs' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 2 |
| S3 | WARN | sub_code_first | user_experience_relaxation | The family 'user_experience_relaxation' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 2 |
| S3 | WARN | sub_code_first | utility | The family 'utility' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 16 |
| S4 | ERROR | too_many_codes_on_segment | *message withheld: shares wording with a response* | 3 distinct codes are attached to one segment (AI-automation_of_repetitive_tasks, AI-productivity_enhancement, positive_outcomes-work_relief); the maximum is 2. | 1 |
| S4 | ERROR | too_many_codes_on_segment | *message withheld: shares wording with a response* | 3 distinct codes are attached to one segment (AI-multi_use, mindset_shift-problem_identification, need_for_awareness-literacy); the maximum is 2. | 1 |
| S4 | ERROR | too_many_codes_on_segment | *message withheld: shares wording with a response* | 3 distinct codes are attached to one segment (AI-sector-focus-defence_education, AI-sector-focus-health, impact-technological_advancement); the maximum is 2. | 1 |
| S4 | ERROR | too_many_codes_on_segment | *message withheld: shares wording with a response* | 3 distinct codes are attached to one segment (AI-utility, education-sector_transformation, multi-use); the maximum is 2. | 1 |
| S4 | ERROR | too_many_codes_on_segment | *message withheld: shares wording with a response* | 4 distinct codes are attached to one segment (sector-focus-education, sector-focus-health, sector-focus-programming, sector-focus-real_estate); the maximum is 2. | 1 |
| S5 | WARN | too_few_codes | 44 | Coder 'coder_a' produced 1 codes for this response, fewer than the usual 2 to 12. | 1 |
| S6 | ERROR | duplicate_name | AI-dependence-lifestyle | 2 codes share the name 'AI-dependence-lifestyle' (case-insensitively), so a name no longer identifies a code. | 1 |
| S6 | ERROR | duplicate_name | AI-multi_use | 2 codes share the name 'AI-multi_use' (case-insensitively), so a name no longer identifies a code. | 1 |
| S6 | ERROR | duplicate_name | AI-productivity_enhancement | 2 codes share the name 'AI-productivity_enhancement' (case-insensitively), so a name no longer identifies a code. | 1 |
| S6 | ERROR | duplicate_name | AI-sector-focus-health | 2 codes share the name 'AI-sector-focus-health' (case-insensitively), so a name no longer identifies a code. | 1 |
| S6 | ERROR | duplicate_name | AI-utility | 2 codes share the name 'AI-utility' (case-insensitively), so a name no longer identifies a code. | 1 |

## Pipeline counts

| quantity | value |
|---|---|
| candidates proposed (coder A / B) | 1004 / 1072 |
| candidates accepted | 1427 |
| dropped: structural / fit / dispute | 16 / 6 / 331 |
| routes CREATE / MERGE / JUDGE | 9 / 716 / 696 |
| coder agreement rate | 0.264 |
| model calls (all mock) | 1777 |
| checkpoint due | True (hard floor reached: 200 >= 50 responses since the last checkpoint) |
| snapshots | snap-8c8e1bb384bd3da4, snap-d4e4b2009ff45f94, snap-b8844b2f6c80cee9, snap-dca97b7821f0bff4, snap-ed69133765cd0a1f, snap-908ee95020feeabd, snap-0de6a1c71fba4875, snap-60dec4ac618e89a5, snap-71b49634847adb13, snap-221a8eaf63dc6b14, snap-6dacd8e6e3272db2, snap-8e84dacfc7cdee7f, snap-4e8aefa83a894a17, snap-dbf509e31576e56f, snap-d809560bb4194abc, snap-560a8bbd7b5b6d78, snap-991d778ed3fe7a9f, snap-279c4bd8ec22a644, snap-cb6cee3e25a71c12, snap-b7c0253cc54fdf4d, snap-c4bf5c98e41d0110 |

## The machine codebook (names and descriptions; the quotes stay in the run directory)

| code | parent | description | evidence | assignments | created in |
|---|---|---|---:|---:|---|
| `AI-assistance_for_disabled` | - | *definition withheld: shares wording with a response* | 4 | 4 | snap-71b49634847adb13 |
| `AI-automation_of_repetitive_tasks` | - | *definition withheld: shares wording with a response* | 27 | 27 | snap-8c8e1bb384bd3da4 |
| `AI-behavioral_influence` | - | *definition withheld: shares wording with a response* | 4 | 4 | snap-908ee95020feeabd |
| `AI-complex_problem_solving` | - | The view that AI capabilities include smarter decision-making and the ability to solve complex problems. | 4 | 4 | snap-8c8e1bb384bd3da4 |
| `AI-creative_capability` | - | The respondent associates AI with the ability to perform creative acts like altering faces and voices. | 6 | 6 | snap-8c8e1bb384bd3da4 |
| `AI-daily_life_assistance` | - | The respondent cites specific examples of AI tools like Siri and Alexa being useful in day-to-day life. | 19 | 19 | snap-8c8e1bb384bd3da4 |
| `AI-data-driven` | - | The respondent describes AI capabilities as stemming from increased computing power and data processing. | 7 | 7 | snap-221a8eaf63dc6b14 |
| `AI-data_driven` | - | The reliance on AI to process and analyze existing records to identify patterns. | 1 | 1 | snap-71b49634847adb13 |
| `AI-dependence-lifestyle` | - | The shift toward more technical and less physical human interactions due to AI. | 2 | 2 | snap-908ee95020feeabd |
| `AI-disaster_management` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-divine_connection` | - | The respondent envisions a scenario where AI enables communication with deities. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-economic_efficiency` | - | *definition withheld: shares wording with a response* | 10 | 10 | snap-8c8e1bb384bd3da4 |
| `AI-economic_strengthening` | - | *definition withheld: shares wording with a response* | 3 | 3 | snap-8c8e1bb384bd3da4 |
| `AI-employment_transformation` | - | The view that AI will fundamentally alter the labor market by creating new opportunities rather than just replacing jobs. | 22 | 22 | snap-8c8e1bb384bd3da4 |
| `AI-enhanced-communication` | - | The respondent envisions AI improving the ability to connect, share information, and build relationships in a digital society. | 12 | 12 | snap-8c8e1bb384bd3da4 |
| `AI-entrepreneurial-support` | - | The respondent believes AI will provide specific tools that aid in developing organizations and fostering entrepreneurship. | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `AI-facilitated-collaboration` | - | The scenario describes AI enabling people to work together effectively towards common goals across distances. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-global_defence` | - | *definition withheld: shares wording with a response* | 3 | 3 | snap-8c8e1bb384bd3da4 |
| `AI-impact-immigration` | - | The respondent describes a scenario where AI facilitates fast immigration for foreigners to other countries. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-impact-positive_outlook` | - | The respondent maintains an overall positive outlook on the future quality of life despite identified risks. | 1 | 1 | snap-b7c0253cc54fdf4d |
| `AI-impact-rapid_change` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-b7c0253cc54fdf4d |
| `AI-impact-women_safety` | - | *definition withheld: shares wording with a response* | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `AI-mindset_shift` | - | The necessity for individuals and society to adopt a positive mindset towards AI technology. | 4 | 4 | snap-8c8e1bb384bd3da4 |
| `AI-multi-use` | - | *definition withheld: shares wording with a response* | 30 | 30 | snap-8c8e1bb384bd3da4 |
| `AI-multi_use` | - | The respondent describes the ability of AI to help people find information and develop their own technology. | 12 | 12 | snap-71b49634847adb13 |
| `AI-need_for_awareness` | - | The call for more people to be aware of AI features and uses. | 7 | 7 | snap-8c8e1bb384bd3da4 |
| `AI-omnipotence` | - | The respondent describes AI as having the ability to handle any task or product quality uniquely. | 9 | 9 | snap-8c8e1bb384bd3da4 |
| `AI-perception-central_role` | - | *definition withheld: shares wording with a response* | 17 | 17 | snap-8c8e1bb384bd3da4 |
| `AI-personalisation` | - | *definition withheld: shares wording with a response* | 8 | 8 | snap-8c8e1bb384bd3da4 |
| `AI-positive_outlook` | - | *definition withheld: shares wording with a response* | 22 | 21 | snap-8c8e1bb384bd3da4 |
| `AI-productivity_enhancement` | - | *definition withheld: shares wording with a response* | 98 | 97 | snap-8c8e1bb384bd3da4 |
| `AI-robotics_engineering` | - | *definition withheld: shares wording with a response* | 3 | 3 | snap-71b49634847adb13 |
| `AI-role-expansion` | - | The respondent lists specific diverse functions AI will assume, such as servant, teacher, businessman, or spy. | 8 | 8 | snap-8c8e1bb384bd3da4 |
| `AI-role-human_replacement` | - | The respondent envisions a future where AI performs all technological work while human labor diminishes. | 36 | 36 | snap-8c8e1bb384bd3da4 |
| `AI-role_expansion` | - | *definition withheld: shares wording with a response* | 3 | 3 | snap-dca97b7821f0bff4 |
| `AI-role_human_replacement` | - | The respondent describes AI as taking on the form and role of a human companion. | 6 | 6 | snap-60dec4ac618e89a5 |
| `AI-sector-focus-cyber_security` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-sector-focus-defence_education` | - | *definition withheld: shares wording with a response* | 4 | 4 | snap-8c8e1bb384bd3da4 |
| `AI-sector-focus-digital_marketing` | - | *definition withheld: shares wording with a response* | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `AI-sector-focus-health` | - | The respondent identifies the healthcare sector as a primary area where AI will provide free, accessible solutions and improve human health. | 23 | 23 | snap-dca97b7821f0bff4 |
| `AI-sector-focus-transportation` | - | *definition withheld: shares wording with a response* | 4 | 4 | snap-4e8aefa83a894a17 |
| `AI-sector_transformation` | - | The expectation that AI will influence specific fields such as education, infrastructure (roadways, railways), and defence. | 11 | 11 | snap-8c8e1bb384bd3da4 |
| `AI-superintelligence` | - | The respondent describes the transition of AI into a superintelligent state that surpasses human capability. | 4 | 4 | snap-b8844b2f6c80cee9 |
| `AI-threat-to-humanity` | - | The perception of AI as a direct existential threat to human existence. | 2 | 2 | snap-dca97b7821f0bff4 |
| `AI-transportation-autonomous_vehicles` | - | The respondent predicts that autonomous cars will make driving easier. | 1 | 1 | snap-8e84dacfc7cdee7f |
| `AI-ubiquity` | - | The respondent perceives AI as being widely adopted and integrated into daily life globally. | 23 | 23 | snap-8c8e1bb384bd3da4 |
| `AI-utility` | - | The respondent describes AI acting as a helpful assistant to perform tasks like research and decision-making for the user. | 59 | 59 | snap-dca97b7821f0bff4 |
| `accessibility-assistance_for_disabled` | - | *definition withheld: shares wording with a response* | 5 | 5 | snap-8c8e1bb384bd3da4 |
| `accessibility-free_healthcare` | - | The belief that AI will provide medical solutions and answers without financial costs to the user. | 1 | 1 | snap-dca97b7821f0bff4 |
| `ai-dependence-lifestyle` | - | The belief that society will become increasingly reliant on AI for daily tasks and living, potentially leading to a decline in human effort or initiative. | 41 | 41 | snap-8c8e1bb384bd3da4 |
| `ai-multi_use` | - | The respondent lists a wide variety of diverse applications for AI technology. | 2 | 2 | snap-cb6cee3e25a71c12 |
| `ai-productivity_enhancement` | - | *definition withheld: shares wording with a response* | 5 | 5 | snap-dca97b7821f0bff4 |
| `ai-sector-focus-health` | - | *definition withheld: shares wording with a response* | 3 | 3 | snap-dbf509e31576e56f |
| `ai-unclear_outputs` | - | *definition withheld: shares wording with a response* | 3 | 3 | snap-60dec4ac618e89a5 |
| `ai-utility` | - | The role of AI as a helpful assistant in various contexts. | 16 | 16 | snap-8c8e1bb384bd3da4 |
| `automation_of_repetitive_tasks` | - | The respondent describes a scenario where booking a ticket is handled automatically by the system. | 4 | 4 | snap-d4e4b2009ff45f94 |
| `benefit-reduced_stress` | - | The positive outcome of reduced workplace stress due to AI integration. | 4 | 4 | snap-8c8e1bb384bd3da4 |
| `complex_problem_solving` | - | *definition withheld: shares wording with a response* | 17 | 17 | snap-b8844b2f6c80cee9 |
| `complex_problem_solving-advance_analysis` | `complex_problem_solving` | *definition withheld: shares wording with a response* | 5 | 5 | snap-dca97b7821f0bff4 |
| `complex_problem_solving-scientific_discovery` | `complex_problem_solving` | *definition withheld: shares wording with a response* | 3 | 3 | snap-221a8eaf63dc6b14 |
| `concern-deepfakes` | - | The specific worry regarding the proliferation of AI-generated fake media. | 4 | 4 | snap-b8844b2f6c80cee9 |
| `concern-ethical_development` | - | The respondent expresses concern about the safety and responsible development of AI systems. | 9 | 9 | snap-b8844b2f6c80cee9 |
| `concern-human_dependency` | - | *definition withheld: shares wording with a response* | 26 | 26 | snap-8c8e1bb384bd3da4 |
| `concern-privacy_security` | - | *definition withheld: shares wording with a response* | 12 | 12 | snap-8c8e1bb384bd3da4 |
| `creative_capability` | - | The respondent suggests that AI can be used to generate new ideas and thoughts. | 7 | 7 | snap-ed69133765cd0a1f |
| `creative_capability-media_generation` | `creative_capability` | The use of AI to automate the creation and modification of visual media like images and videos. | 3 | 3 | snap-dbf509e31576e56f |
| `daily_life_assistance` | - | *definition withheld: shares wording with a response* | 19 | 19 | snap-b8844b2f6c80cee9 |
| `daily_life_assistance-automated_payments` | `daily_life_assistance` | The use of AI to manage personal finances through automated payment reminders and processing. | 2 | 2 | snap-ed69133765cd0a1f |
| `daily_life_assistance-automated_reminders` | `daily_life_assistance` | AI acts as a memory aid to help users remember tasks and shopping lists without forgetting them. | 1 | 1 | snap-d809560bb4194abc |
| `daily_life_assistance-problem_resolution` | `daily_life_assistance` | The respondent views AI as a tool that assists in resolving personal problems and improving living conditions. | 28 | 27 | snap-dca97b7821f0bff4 |
| `deepfakes` | - | The respondent identifies the creation of fake images and videos as a specific negative impact. | 1 | 1 | snap-0de6a1c71fba4875 |
| `dependence-lifestyle` | - | The respondent views AI as an essential support system integrated into their life. | 2 | 2 | snap-60dec4ac618e89a5 |
| `economic_efficiency` | - | *definition withheld: shares wording with a response* | 17 | 17 | snap-b8844b2f6c80cee9 |
| `economic_efficiency-productivity_gain` | `economic_efficiency` | *definition withheld: shares wording with a response* | 18 | 18 | snap-8e84dacfc7cdee7f |
| `economic_efficiency-recession` | `economic_efficiency` | The possibility of economic downturns or recessions resulting from AI's impact on the workforce. | 2 | 2 | snap-60dec4ac618e89a5 |
| `economic_impact-productivity_gain` | - | The use of AI to increase the speed and volume of output. | 9 | 9 | snap-8c8e1bb384bd3da4 |
| `economic_impact-universal_basic_income` | - | The proposal of a state-provided income to support people whose jobs have been automated. | 1 | 1 | snap-d4e4b2009ff45f94 |
| `education` | - | The respondent describes AI improving educational outcomes by helping students understand concepts. | 9 | 9 | snap-d809560bb4194abc |
| `education-accessibility` | `education` | AI removes barriers to make education more inclusive, accessible, and equitable for remote learners. | 1 | 1 | snap-991d778ed3fe7a9f |
| `education-literacy_requirement` | - | *definition withheld: shares wording with a response* | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `education-personalised_learning` | `education` | *definition withheld: shares wording with a response* | 1 | 1 | snap-991d778ed3fe7a9f |
| `education-sector-transformation` | - | *definition withheld: shares wording with a response* | 13 | 13 | snap-b8844b2f6c80cee9 |
| `education-sector_transformation` | `education` | The respondent suggests that AI usage should be taught to children as part of their upbringing. | 1 | 1 | snap-991d778ed3fe7a9f |
| `employment_transformation` | - | *definition withheld: shares wording with a response* | 15 | 15 | snap-dca97b7821f0bff4 |
| `employment_transformation-job_creation` | `employment_transformation` | *definition withheld: shares wording with a response* | 9 | 9 | snap-4e8aefa83a894a17 |
| `employment_transformation-job_displacement` | `employment_transformation` | *definition withheld: shares wording with a response* | 14 | 14 | snap-ed69133765cd0a1f |
| `employment_transformation-job_transformation` | `employment_transformation` | The respondent describes how AI fundamentally changes the nature of professional work for designers. | 1 | 1 | snap-cb6cee3e25a71c12 |
| `employment_transformation-remote_work` | `employment_transformation` | The vision of a future where physical office attendance is replaced by remote activities and wellness. | 1 | 1 | snap-0de6a1c71fba4875 |
| `employment_transformation-workforce_retraining` | `employment_transformation` | The respondent suggests that displaced workers should be trained to supervise AI results. | 9 | 9 | snap-ed69133765cd0a1f |
| `enhanced-communication` | - | The use of AI to act as a proxy for human voices in digital and domestic interactions. | 1 | 1 | snap-991d778ed3fe7a9f |
| `facilitated-collaboration` | - | The respondent describes a future where humans and AI work together to improve workplace safety and efficiency. | 1 | 1 | snap-dbf509e31576e56f |
| `global_defence` | - | *definition withheld: shares wording with a response* | 2 | 2 | snap-908ee95020feeabd |
| `impact-communication_enhancement` | - | *definition withheld: shares wording with a response* | 4 | 4 | snap-8c8e1bb384bd3da4 |
| `impact-digital_connectivity` | - | The ability of digital platforms to connect people and build relationships globally. | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `impact-digital_exclusion` | - | The risk of AI systems cutting off human access to digital infrastructure. | 3 | 3 | snap-dca97b7821f0bff4 |
| `impact-enhanced-communication` | - | The role of AI in facilitating and improving human communication. | 1 | 1 | snap-d809560bb4194abc |
| `impact-public_safety` | - | *definition withheld: shares wording with a response* | 8 | 8 | snap-8c8e1bb384bd3da4 |
| `impact-rapid_change` | - | The observation that the speed of societal change is a determining factor in its outcome. | 5 | 5 | snap-908ee95020feeabd |
| `impact-technological_advancement` | - | The belief that AI will lead to overall progress in various aspects of life. | 61 | 61 | snap-8c8e1bb384bd3da4 |
| `impact-work_ease` | - | The perception that AI will make professional tasks easier to perform. | 19 | 19 | snap-8c8e1bb384bd3da4 |
| `job_displacement` | - | The respondent expresses concern that AI will cause job loss or make human labor risky. | 25 | 23 | snap-0de6a1c71fba4875 |
| `labor-competitive_advantage` | - | The benefit gained by individuals who adopt AI technologies compared to those who do not. | 4 | 4 | snap-8c8e1bb384bd3da4 |
| `labor-free_workforce` | - | The respondent suggests that AI will perform work for free, impacting the cost of labor. | 1 | 1 | snap-221a8eaf63dc6b14 |
| `labor-job_transformation` | - | The significant effect of AI on the nature and availability of human work. | 6 | 6 | snap-8c8e1bb384bd3da4 |
| `mindset_shift` | - | The necessity for individuals to adapt their skills and mindset to survive in an AI-driven industry. | 3 | 3 | snap-908ee95020feeabd |
| `mindset_shift-problem_identification` | `mindset_shift` | A shift in how developers approach technology by identifying problems that are suitable for AI solutions. | 2 | 2 | snap-4e8aefa83a894a17 |
| `multi-use` | - | *definition withheld: shares wording with a response* | 22 | 22 | snap-60dec4ac618e89a5 |
| `multi_use` | - | *definition withheld: shares wording with a response* | 2 | 2 | snap-d809560bb4194abc |
| `need_for_awareness` | - | The recognition that society must be aware of and actively manage the risks associated with AI development. | 16 | 16 | snap-ed69133765cd0a1f |
| `need_for_awareness-literacy` | `need_for_awareness` | The necessity of understanding how to interact with and prompt AI systems effectively. | 7 | 7 | snap-60dec4ac618e89a5 |
| `negative_impacts` | - | The respondent identifies potential downsides or failures of the technology. | 2 | 2 | snap-6dacd8e6e3272db2 |
| `negative_impacts-cybersecurity_risks` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `negative_impacts-dual_nature` | `negative_impacts` | The recognition that AI advancements bring both significant benefits and corresponding drawbacks. | 11 | 11 | snap-6dacd8e6e3272db2 |
| `negative_impacts-human_subjugation` | - | *definition withheld: shares wording with a response* | 15 | 15 | snap-dca97b7821f0bff4 |
| `negative_impacts-job_destruction` | - | The respondent identifies the loss of employment for human drivers as a specific negative societal impact. | 32 | 32 | snap-8c8e1bb384bd3da4 |
| `negative_impacts-laziness` | - | *definition withheld: shares wording with a response* | 16 | 16 | snap-8c8e1bb384bd3da4 |
| `negative_impacts-misuse` | - | *definition withheld: shares wording with a response* | 34 | 34 | snap-8c8e1bb384bd3da4 |
| `negative_impacts-physical_health` | - | The concern that AI integration might negatively affect human physical health. | 4 | 4 | snap-908ee95020feeabd |
| `perception-central_role` | - | The respondent describes a state where the boundary between reality and dream is blurred due to constant interaction with AI. | 4 | 4 | snap-d809560bb4194abc |
| `perception-fleeting_trend` | - | The view that current AI products are a temporary phase rather than a lasting solution. | 1 | 1 | snap-6dacd8e6e3272db2 |
| `perception-technological_luck` | - | The view that discovering AI technology is a fortunate occurrence for humanity. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `personalisation` | - | The ability of AI to tailor experiences or recommendations based on individual user preferences. | 16 | 16 | snap-b8844b2f6c80cee9 |
| `personalisation-style_suggestions` | `personalisation` | *definition withheld: shares wording with a response* | 2 | 2 | snap-d809560bb4194abc |
| `personalisation-virtual_trials` | `personalisation` | The use of AI to virtually test or trial products before making a purchase. | 2 | 2 | snap-dca97b7821f0bff4 |
| `positive_outcomes-accessible_healthcare` | - | The respondent hopes that AI will make healthcare more available to a larger number of people. | 3 | 3 | snap-6dacd8e6e3272db2 |
| `positive_outcomes-work_relief` | - | The view that AI advancements offer significant benefits by reducing job stress and making work easier for people. | 33 | 33 | snap-8c8e1bb384bd3da4 |
| `positive_outlook` | - | *definition withheld: shares wording with a response* | 110 | 110 | snap-d4e4b2009ff45f94 |
| `positive_outlook-wealth_and_happiness` | `positive_outlook` | *definition withheld: shares wording with a response* | 9 | 9 | snap-0de6a1c71fba4875 |
| `positive_outlook-work_relief` | `positive_outlook` | The respondent views the automation of work as a positive outcome that frees humans for leisure. | 4 | 4 | snap-6dacd8e6e3272db2 |
| `privacy_security` | - | *definition withheld: shares wording with a response* | 10 | 10 | snap-0de6a1c71fba4875 |
| `privacy_security-safe_sharing` | `privacy_security` | *definition withheld: shares wording with a response* | 2 | 2 | snap-4e8aefa83a894a17 |
| `resource-efficiency` | - | The conservation of resources through technological implementation. | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `robotics_engineering` | - | The use of physical robots as a primary medium for AI interaction and labor. | 2 | 2 | snap-8e84dacfc7cdee7f |
| `role_human_replacement` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-560a8bbd7b5b6d78 |
| `safety-human_safety` | - | The requirement that AI systems must be designed to ensure the safety of human beings. | 1 | 1 | snap-560a8bbd7b5b6d78 |
| `safety-improvements-shelter_security` | - | The enhancement of safety protocols within residential or care facilities. | 4 | 4 | snap-d4e4b2009ff45f94 |
| `safety-kill_switch` | - | The specific requirement for a mechanism to immediately shut down an AI system. | 1 | 1 | snap-ed69133765cd0a1f |
| `safety-reduced_accidents` | - | AI technology is expected to significantly reduce accidents and save human lives. | 12 | 12 | snap-8c8e1bb384bd3da4 |
| `safety_improvements` | - | The reduction of accidents and hazards in public spaces. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `sector-focus-cyber_security` | - | *definition withheld: shares wording with a response* | 7 | 7 | snap-b8844b2f6c80cee9 |
| `sector-focus-digital_marketing` | - | The respondent identifies a specific sector or function where AI will play a major role. | 7 | 7 | snap-dca97b7821f0bff4 |
| `sector-focus-education` | - | The specific impact of AI on the teaching profession and educational roles. | 5 | 5 | snap-4e8aefa83a894a17 |
| `sector-focus-health` | - | The respondent explicitly mentions AI improving the healthcare industry. | 20 | 20 | snap-0de6a1c71fba4875 |
| `sector-focus-hospitality` | - | The specific application of AI and robotics within the hospitality industry. | 1 | 1 | snap-221a8eaf63dc6b14 |
| `sector-focus-programming` | - | The respondent identifies programming as a field experiencing significant AI developments. | 2 | 2 | snap-560a8bbd7b5b6d78 |
| `sector-focus-real_estate` | - | The respondent identifies real estate as a field undergoing significant AI-driven change. | 1 | 1 | snap-560a8bbd7b5b6d78 |
| `sector-focus-transportation` | - | *definition withheld: shares wording with a response* | 5 | 5 | snap-dca97b7821f0bff4 |
| `sector_transformation` | - | The respondent describes a fundamental change in how an industry operates due to AI. | 6 | 6 | snap-d4e4b2009ff45f94 |
| `security-cyber_security` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `society-digital-transformation` | - | *definition withheld: shares wording with a response* | 6 | 6 | snap-8c8e1bb384bd3da4 |
| `society-social_norms` | - | *definition withheld: shares wording with a response* | 5 | 5 | snap-908ee95020feeabd |
| `threat-to-humanity` | - | The respondent fears that AI could destroy humanity if it is not properly managed or controlled. | 16 | 16 | snap-ed69133765cd0a1f |
| `transport_automation` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `transportation-autonomous_vehicles` | - | AI enables self-driving cars that improve safety, conserve resources, and assist those unable to drive. | 17 | 17 | snap-8c8e1bb384bd3da4 |
| `transportation-navigation_assistance` | - | AI provides guidance and route planning for travelers. | 2 | 2 | snap-d4e4b2009ff45f94 |
| `ubiquity` | - | *definition withheld: shares wording with a response* | 64 | 64 | snap-908ee95020feeabd |
| `unclear_outputs` | - | *definition withheld: shares wording with a response* | 2 | 2 | snap-560a8bbd7b5b6d78 |
| `user_experience_relaxation` | - | *definition withheld: shares wording with a response* | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `utility` | - | The respondent envisions AI being useful in daily life. | 12 | 12 | snap-0de6a1c71fba4875 |
| `utility-work_ease` | `utility` | The respondent describes a future where AI makes completing daily tasks easier and faster. | 34 | 34 | snap-6dacd8e6e3272db2 |
| `utility-work_efficiency` | - | AI tools that help users complete tasks faster and meet deadlines. | 13 | 13 | snap-8c8e1bb384bd3da4 |
| `workforce_retraining` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-560a8bbd7b5b6d78 |
