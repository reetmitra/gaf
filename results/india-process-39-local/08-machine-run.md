# 08 - The machine run (live-model coders), run id `local-eval39`

39 responses, 291 segments, 316 assignments, 91 codes in 31 families; embedding space `local-embeddinggemma-768`; offline: False.

**Caveats the run printed about itself:**


The two most-used machine codes account for 32 of 316 assignments: `AI-productivity_enhancement` 18, `AI-ubiquity` 14. Read it as a property of these coders on this sample.

## Findings by check

| check | ERROR | WARN | INFO |
|---|---:|---:|---:|
| M1 | 0 | 164 | 56 |
| M2 | 0 | 162 | 112 |
| M3 | 0 | 5 | 312 |
| S1 | 1 | 0 | 0 |
| S2 | 2 | 0 | 2 |
| S2b | 0 | 4 | 0 |
| S3 | 0 | 27 | 0 |
| S5 | 0 | 1 | 0 |
| S6 | 2 | 0 | 3 |

## Findings by marker

| check | severity | marker | n |
|---|---|---|---:|
| M1 | INFO | coders_agree | 56 |
| M1 | WARN | coder_unmatched | 45 |
| M1 | WARN | coders_dispute | 6 |
| M1 | WARN | grey_zone_judged | 113 |
| M2 | INFO | route_create | 8 |
| M2 | INFO | route_merge | 104 |
| M2 | WARN | route_judge | 162 |
| M3 | INFO | fit_ok | 312 |
| M3 | WARN | fit_incomplete | 5 |
| S1 | ERROR | missing_evidence | 1 |
| S2 | ERROR | no_verified_evidence | 2 |
| S2 | INFO | quote_unverified | 2 |
| S2b | WARN | quote_too_long | 4 |
| S3 | WARN | sub_code_first | 27 |
| S5 | WARN | too_few_codes | 1 |
| S6 | ERROR | duplicate_name | 2 |
| S6 | INFO | evidence_on_parent | 3 |

## Every ERROR and WARN (subject is the candidate or response concerned)

| check | severity | marker | subject | message | n |
|---|---|---|---|---|---:|
| M1 | WARN | coder_unmatched | (unmatched)<->AI-enhanced-communication | Coder B proposed 'AI-enhanced-communication' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-multi-use | Coder B proposed 'AI-multi-use' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-productivity_enhancement | Coder B proposed 'AI-productivity_enhancement' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-threat-to-humanity | Coder B proposed 'AI-threat-to-humanity' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->AI-ubiquity | Coder B proposed 'AI-ubiquity' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->accessibility-free_healthcare | Coder B proposed 'accessibility-free_healthcare' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->ai-role-human_replacement | Coder B proposed 'ai-role-human_replacement' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->ai-ubiquity | Coder B proposed 'ai-ubiquity' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->ai-utility | Coder B proposed 'ai-utility' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->automation_of_repetitive_tasks | Coder B proposed 'automation_of_repetitive_tasks' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->concern-human_dependency | Coder B proposed 'concern-human_dependency' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->economic_impact-productivity_gain | Coder B proposed 'economic_impact-productivity_gain' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->education-literacy_requirement | Coder B proposed 'education-literacy_requirement' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->impact-communication_enhancement | Coder B proposed 'impact-communication_enhancement' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->impact-digital_exclusion | Coder B proposed 'impact-digital_exclusion' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->impact-technological_advancement | Coder B proposed 'impact-technological_advancement' and the other coder proposed nothing that could be assigned to it. | 4 |
| M1 | WARN | coder_unmatched | (unmatched)<->impact-work_ease | Coder B proposed 'impact-work_ease' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->labor-competitive_advantage | Coder B proposed 'labor-competitive_advantage' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->labor-job_transformation | Coder B proposed 'labor-job_transformation' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->negative_impacts-job_destruction | Coder B proposed 'negative_impacts-job_destruction' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->resource-efficiency | Coder B proposed 'resource-efficiency' and the other coder proposed nothing that could be assigned to it. | 2 |
| M1 | WARN | coder_unmatched | (unmatched)<->safety_improvements | Coder B proposed 'safety_improvements' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->sector-focus-transportation | Coder B proposed 'sector-focus-transportation' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->society-digital-transformation | Coder B proposed 'society-digital-transformation' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->transport_automation | Coder B proposed 'transport_automation' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->transportation-navigation_assistance | Coder B proposed 'transportation-navigation_assistance' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->utility-efficiency_gain | Coder B proposed 'utility-efficiency_gain' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | (unmatched)<->utility-work_efficiency | Coder B proposed 'utility-work_efficiency' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | AI-automation_of_repetitive_tasks<->(unmatched) | Coder A proposed 'AI-automation_of_repetitive_tasks' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | AI-global_defence<->(unmatched) | Coder A proposed 'AI-global_defence' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | AI-perception-central_role<->(unmatched) | Coder A proposed 'AI-perception-central_role' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | concern-human_dependency<->(unmatched) | Coder A proposed 'concern-human_dependency' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | negative_impacts-misuse<->(unmatched) | Coder A proposed 'negative_impacts-misuse' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | positive_outlook<->(unmatched) | Coder A proposed 'positive_outlook' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | sector-focus-digital_marketing<->(unmatched) | Coder A proposed 'sector-focus-digital_marketing' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coder_unmatched | transportation-autonomous_vehicles<->(unmatched) | Coder A proposed 'transportation-autonomous_vehicles' and the other coder proposed nothing that could be assigned to it. | 1 |
| M1 | WARN | coders_dispute | AI-productivity_enhancement<->personalisation-virtual_trials | Coders dispute: 'AI-productivity_enhancement' and 'personalisation-virtual_trials' match at only cosine 0.413 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | AI-role-expansion<->education-literacy_requirement | Coders dispute: 'AI-role-expansion' and 'education-literacy_requirement' match at only cosine 0.399 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | AI-sector-focus-cyber_security<->security-cyber_security | Coders dispute: 'AI-sector-focus-cyber_security' and 'security-cyber_security' match at only cosine 0.423 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | perception-central_role<->AI-multi-use | Coders dispute: 'perception-central_role' and 'AI-multi-use' match at only cosine 0.414 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | positive_outlook<->AI-enhanced-communication | Coders dispute: 'positive_outlook' and 'AI-enhanced-communication' match at only cosine 0.432 (< tau_low 0.45). | 1 |
| M1 | WARN | coders_dispute | positive_outlook<->safety-improvements-shelter_security | Coders dispute: 'positive_outlook' and 'safety-improvements-shelter_security' match at only cosine 0.214 (< tau_low 0.45). | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->AI-daily_life_assistance | Grey zone ruled KEEP: 'AI-automation_of_repetitive_tasks' and 'AI-daily_life_assistance' match at cosine 0.678, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->AI-productivity_enhancement | Grey zone ruled KEEP: 'AI-automation_of_repetitive_tasks' and 'AI-productivity_enhancement' match at cosine 0.539, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-automation_of_repetitive_tasks<->utility-operational_automation | Grey zone ruled DROP: 'AI-automation_of_repetitive_tasks' and 'utility-operational_automation' match at cosine 0.784, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-complex_problem_solving<->utility-problem_solving | Grey zone ruled DROP: 'AI-complex_problem_solving' and 'utility-problem_solving' match at cosine 0.741, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-creative_capability<->technology-media_manipulation | Grey zone ruled DROP: 'AI-creative_capability' and 'technology-media_manipulation' match at cosine 0.655, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-daily_life_assistance<->ai-dependence-lifestyle | Grey zone ruled KEEP: 'AI-daily_life_assistance' and 'ai-dependence-lifestyle' match at cosine 0.590, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-daily_life_assistance<->utility-daily_assistance | Grey zone ruled DROP: 'AI-daily_life_assistance' and 'utility-daily_assistance' match at cosine 0.607, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-disaster_management<->impact-public_safety | Grey zone ruled KEEP: 'AI-disaster_management' and 'impact-public_safety' match at cosine 0.577, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-divine_connection<->culture-religious_integration | Grey zone ruled DROP: 'AI-divine_connection' and 'culture-religious_integration' match at cosine 0.565, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-economic_efficiency<->AI-perception-central_role | Grey zone ruled KEEP: 'AI-economic_efficiency' and 'AI-perception-central_role' match at cosine 0.601, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-economic_efficiency<->economic_impact-cost_reduction | Grey zone ruled DROP: 'AI-economic_efficiency' and 'economic_impact-cost_reduction' match at cosine 0.748, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-efficiency<->utility-time_reduction | Grey zone ruled DROP: 'AI-efficiency' and 'utility-time_reduction' match at cosine 0.681, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-employment_transformation<->labor-job_transformation | Grey zone ruled KEEP: 'AI-employment_transformation' and 'labor-job_transformation' match at cosine 0.649, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-employment_transformation<->personalisation | Grey zone ruled KEEP: 'AI-employment_transformation' and 'personalisation' match at cosine 0.478, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-enhanced-communication<->impact-digital_connectivity | Grey zone ruled KEEP: 'AI-enhanced-communication' and 'impact-digital_connectivity' match at cosine 0.512, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-entrepreneurial-support<->ai_utility-organizational_tools | Grey zone ruled DROP: 'AI-entrepreneurial-support' and 'ai_utility-organizational_tools' match at cosine 0.697, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-facilitated-collaboration<->impact-collaborative_work | Grey zone ruled DROP: 'AI-facilitated-collaboration' and 'impact-collaborative_work' match at cosine 0.556, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-impact-immigration<->migration-easier_immigration | Grey zone ruled DROP: 'AI-impact-immigration' and 'migration-easier_immigration' match at cosine 0.572, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-impact-women_safety<->safety-women_safety | Grey zone ruled DROP: 'AI-impact-women_safety' and 'safety-women_safety' match at cosine 0.723, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-mindset_shift<->attitude-mindset_shift | Grey zone ruled DROP: 'AI-mindset_shift' and 'attitude-mindset_shift' match at cosine 0.751, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-multi-use<->AI-employment_transformation | Grey zone ruled KEEP: 'AI-multi-use' and 'AI-employment_transformation' match at cosine 0.549, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-multi-use<->AI-multi-use | Grey zone ruled DROP: 'AI-multi-use' and 'AI-multi-use' match at cosine 0.758, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-omnipotence<->AI-multi-use | Grey zone ruled DROP: 'AI-omnipotence' and 'AI-multi-use' match at cosine 0.604, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-omnipotence<->AI-omnipotence | Grey zone ruled DROP: 'AI-omnipotence' and 'AI-omnipotence' match at cosine 0.721, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-omnipotence<->ai-reliability | Grey zone ruled DROP: 'AI-omnipotence' and 'ai-reliability' match at cosine 0.607, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-personalisation<->utility-personalization | Grey zone ruled DROP: 'AI-personalisation' and 'utility-personalization' match at cosine 0.738, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-positive_outlook<->impact-positive_outcomes | Grey zone ruled DROP: 'AI-positive_outlook' and 'impact-positive_outcomes' match at cosine 0.625, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-positive_outlook<->impact-technological_advancement | Grey zone ruled KEEP: 'AI-positive_outlook' and 'impact-technological_advancement' match at cosine 0.588, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-positive_outlook<->utility-work_efficiency | Grey zone ruled KEEP: 'AI-positive_outlook' and 'utility-work_efficiency' match at cosine 0.465, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->AI-productivity_enhancement | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'AI-productivity_enhancement' match at cosine 0.744, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->ai-utility | Grey zone ruled KEEP: 'AI-productivity_enhancement' and 'ai-utility' match at cosine 0.556, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->utility-efficiency_gains | Grey zone ruled DROP: 'AI-productivity_enhancement' and 'utility-efficiency_gains' match at cosine 0.702, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-productivity_enhancement<->utility-work_efficiency | Grey zone ruled KEEP: 'AI-productivity_enhancement' and 'utility-work_efficiency' match at cosine 0.555, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-expansion<->AI-superintelligence | Grey zone ruled KEEP: 'AI-role-expansion' and 'AI-superintelligence' match at cosine 0.598, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-expansion<->ai-versatility | Grey zone ruled DROP: 'AI-role-expansion' and 'ai-versatility' match at cosine 0.660, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->AI-role-human_replacement | Grey zone ruled DROP: 'AI-role-human_replacement' and 'AI-role-human_replacement' match at cosine 0.657, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->impact-public_safety | Grey zone ruled KEEP: 'AI-role-human_replacement' and 'impact-public_safety' match at cosine 0.531, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->impact-work_ease | Grey zone ruled KEEP: 'AI-role-human_replacement' and 'impact-work_ease' match at cosine 0.585, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->labor-automation_of_work | Grey zone ruled DROP: 'AI-role-human_replacement' and 'labor-automation_of_work' match at cosine 0.691, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-role-human_replacement<->transportation-autonomous_vehicles | Grey zone ruled KEEP: 'AI-role-human_replacement' and 'transportation-autonomous_vehicles' match at cosine 0.696, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector-focus-defence_education<->sector_impact-defense_and_education | Grey zone ruled DROP: 'AI-sector-focus-defence_education' and 'sector_impact-defense_and_education' match at cosine 0.709, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector-focus-digital_marketing<->marketing-digital_marketing | Grey zone ruled DROP: 'AI-sector-focus-digital_marketing' and 'marketing-digital_marketing' match at cosine 0.604, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-sector_transformation<->impact-infrastructure_improvement | Grey zone ruled DROP: 'AI-sector_transformation' and 'impact-infrastructure_improvement' match at cosine 0.687, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-superintelligence<->AI-superintelligence | Grey zone ruled DROP: 'AI-superintelligence' and 'AI-superintelligence' match at cosine 0.742, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-ubiquity<->AI-ubiquity | Grey zone ruled DROP: 'AI-ubiquity' and 'AI-ubiquity' match at cosine 0.749, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-ubiquity<->ai-multi-use | Grey zone ruled DROP: 'AI-ubiquity' and 'ai-multi-use' match at cosine 0.594, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-ubiquity<->impact-technological_advancement | Grey zone ruled DROP: 'AI-ubiquity' and 'impact-technological_advancement' match at cosine 0.588, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-ubiquity<->perception-technological_luck | Grey zone ruled KEEP: 'AI-ubiquity' and 'perception-technological_luck' match at cosine 0.493, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | AI-utility<->ai-utility | Grey zone ruled DROP: 'AI-utility' and 'ai-utility' match at cosine 0.727, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | accessibility-assistance_for_disabled<->accessibility-inclusive_mobility | Grey zone ruled DROP: 'accessibility-assistance_for_disabled' and 'accessibility-inclusive_mobility' match at cosine 0.754, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-dependence-lifestyle<->ai-dependence-lifestyle | Grey zone ruled DROP: 'ai-dependence-lifestyle' and 'ai-dependence-lifestyle' match at cosine 0.770, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-dependence-lifestyle<->impact-technological_advancement | Grey zone ruled KEEP: 'ai-dependence-lifestyle' and 'impact-technological_advancement' match at cosine 0.681, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-utility<->AI-daily_life_assistance | Grey zone ruled KEEP: 'ai-utility' and 'AI-daily_life_assistance' match at cosine 0.630, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ai-utility<->AI-productivity_enhancement | Grey zone ruled DROP: 'ai-utility' and 'AI-productivity_enhancement' match at cosine 0.657, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | benefit-reduced_stress<->benefit-reduced_stress | Grey zone ruled DROP: 'benefit-reduced_stress' and 'benefit-reduced_stress' match at cosine 0.684, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | complex_problem_solving-advance_analysis<->AI-productivity_enhancement | Grey zone ruled DROP: 'complex_problem_solving-advance_analysis' and 'AI-productivity_enhancement' match at cosine 0.600, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | complex_problem_solving<->complex_problem_solving | Grey zone ruled KEEP: 'complex_problem_solving' and 'complex_problem_solving' match at cosine 0.791, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-ethical_development<->concern-regulatory_oversight | Grey zone ruled DROP: 'concern-ethical_development' and 'concern-regulatory_oversight' match at cosine 0.662, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-human_dependency<->need_for_awareness | Grey zone ruled DROP: 'concern-human_dependency' and 'need_for_awareness' match at cosine 0.611, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-human_dependency<->negative_impacts-misuse | Grey zone ruled KEEP: 'concern-human_dependency' and 'negative_impacts-misuse' match at cosine 0.651, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | concern-privacy_security<->concern-data_privacy | Grey zone ruled DROP: 'concern-privacy_security' and 'concern-data_privacy' match at cosine 0.698, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance-problem_resolution<->AI-positive_outlook | Grey zone ruled KEEP: 'daily_life_assistance-problem_resolution' and 'AI-positive_outlook' match at cosine 0.654, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->daily_life_assistance | Grey zone ruled KEEP: 'daily_life_assistance' and 'daily_life_assistance' match at cosine 0.619, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | daily_life_assistance<->impact-communication_enhancement | Grey zone ruled KEEP: 'daily_life_assistance' and 'impact-communication_enhancement' match at cosine 0.645, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency<->AI-productivity_enhancement | Grey zone ruled DROP: 'economic_efficiency' and 'AI-productivity_enhancement' match at cosine 0.677, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_efficiency<->economic_impact-productivity_gain | Grey zone ruled KEEP: 'economic_efficiency' and 'economic_impact-productivity_gain' match at cosine 0.604, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_impact-productivity_gain<->AI-multi-use | Grey zone ruled DROP: 'economic_impact-productivity_gain' and 'AI-multi-use' match at cosine 0.562, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_impact-productivity_gain<->AI-role_expansion | Grey zone ruled KEEP: 'economic_impact-productivity_gain' and 'AI-role_expansion' match at cosine 0.565, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | economic_impact<->education-sector_transformation | Grey zone ruled KEEP: 'economic_impact' and 'education-sector_transformation' match at cosine 0.550, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | education-sector-transformation<->sector-focus-defence_education | Grey zone ruled DROP: 'education-sector-transformation' and 'sector-focus-defence_education' match at cosine 0.615, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | employment_transformation<->AI-employment_transformation | Grey zone ruled DROP: 'employment_transformation' and 'AI-employment_transformation' match at cosine 0.653, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | impact-technological_advancement<->impact-technological_advancement | Grey zone ruled DROP: 'impact-technological_advancement' and 'impact-technological_advancement' match at cosine 0.775, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | labor-job_transformation<->labor-competitive_advantage | Grey zone ruled KEEP: 'labor-job_transformation' and 'labor-competitive_advantage' match at cosine 0.544, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | labor-job_transformation<->negative_impacts-job_destruction | Grey zone ruled KEEP: 'labor-job_transformation' and 'negative_impacts-job_destruction' match at cosine 0.631, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | labor-job_transformation<->negative_impacts-job_destruction | Grey zone ruled KEEP: 'labor-job_transformation' and 'negative_impacts-job_destruction' match at cosine 0.643, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | multi-use<->impact-technological_advancement | Grey zone ruled KEEP: 'multi-use' and 'impact-technological_advancement' match at cosine 0.476, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-cybersecurity_risks<->concern-cybersecurity | Grey zone ruled DROP: 'negative_impacts-cybersecurity_risks' and 'concern-cybersecurity' match at cosine 0.602, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->concern-human_dependency | Grey zone ruled KEEP: 'negative_impacts-job_destruction' and 'concern-human_dependency' match at cosine 0.695, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->negative_impacts-job_destruction | Grey zone ruled DROP: 'negative_impacts-job_destruction' and 'negative_impacts-job_destruction' match at cosine 0.736, between tau_low 0.45 and tau_high 0.80. | 2 |
| M1 | WARN | grey_zone_judged | negative_impacts-job_destruction<->negative_impacts-job_destruction | Grey zone ruled DROP: 'negative_impacts-job_destruction' and 'negative_impacts-job_destruction' match at cosine 0.754, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-laziness<->concern-loss_of_effort | Grey zone ruled DROP: 'negative_impacts-laziness' and 'concern-loss_of_effort' match at cosine 0.714, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->concern-deepfakes | Grey zone ruled KEEP: 'negative_impacts-misuse' and 'concern-deepfakes' match at cosine 0.519, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->negative_impacts-human_subjugation | Grey zone ruled KEEP: 'negative_impacts-misuse' and 'negative_impacts-human_subjugation' match at cosine 0.545, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->negative_impacts-laziness | Grey zone ruled KEEP: 'negative_impacts-misuse' and 'negative_impacts-laziness' match at cosine 0.647, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->negative_impacts-misuse | Grey zone ruled DROP: 'negative_impacts-misuse' and 'negative_impacts-misuse' match at cosine 0.752, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | negative_impacts-misuse<->risk-malicious_use | Grey zone ruled DROP: 'negative_impacts-misuse' and 'risk-malicious_use' match at cosine 0.736, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | personalisation<->daily_life_assistance | Grey zone ruled KEEP: 'personalisation' and 'daily_life_assistance' match at cosine 0.496, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | personalisation<->personalisation | Grey zone ruled DROP: 'personalisation' and 'personalisation' match at cosine 0.727, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->AI-positive_outlook | Grey zone ruled KEEP: 'positive_outcomes-work_relief' and 'AI-positive_outlook' match at cosine 0.568, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->benefit-reduced_stress | Grey zone ruled KEEP: 'positive_outcomes-work_relief' and 'benefit-reduced_stress' match at cosine 0.768, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->economic_impact-universal_basic_income | Grey zone ruled KEEP: 'positive_outcomes-work_relief' and 'economic_impact-universal_basic_income' match at cosine 0.482, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->impact-work_ease | Grey zone ruled DROP: 'positive_outcomes-work_relief' and 'impact-work_ease' match at cosine 0.664, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outcomes-work_relief<->utility-work_efficiency | Grey zone ruled KEEP: 'positive_outcomes-work_relief' and 'utility-work_efficiency' match at cosine 0.562, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook-better_world<->impact-technological_advancement | Grey zone ruled DROP: 'positive_outlook-better_world' and 'impact-technological_advancement' match at cosine 0.662, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->AI-perception-central_role | Grey zone ruled DROP: 'positive_outlook' and 'AI-perception-central_role' match at cosine 0.755, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->AI-productivity_enhancement | Grey zone ruled KEEP: 'positive_outlook' and 'AI-productivity_enhancement' match at cosine 0.687, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->ai-productivity_enhancement | Grey zone ruled KEEP: 'positive_outlook' and 'ai-productivity_enhancement' match at cosine 0.670, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->impact-technological_advancement | Grey zone ruled KEEP: 'positive_outlook' and 'impact-technological_advancement' match at cosine 0.641, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outlook | Grey zone ruled DROP: 'positive_outlook' and 'positive_outlook' match at cosine 0.727, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | positive_outlook<->positive_outlook | Grey zone ruled DROP: 'positive_outlook' and 'positive_outlook' match at cosine 0.799, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | safety-reduced_accidents<->safety-reduced_accidents | Grey zone ruled DROP: 'safety-reduced_accidents' and 'safety-reduced_accidents' match at cosine 0.682, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector-focus-cyber_security<->sector-focus-cyber_security | Grey zone ruled DROP: 'sector-focus-cyber_security' and 'sector-focus-cyber_security' match at cosine 0.707, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector_transformation<->AI-sector_transformation | Grey zone ruled KEEP: 'sector_transformation' and 'AI-sector_transformation' match at cosine 0.615, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | sector_transformation<->sector-transformation-industrial | Grey zone ruled DROP: 'sector_transformation' and 'sector-transformation-industrial' match at cosine 0.800, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | society-digital-transformation<->impact-communication_enhancement | Grey zone ruled KEEP: 'society-digital-transformation' and 'impact-communication_enhancement' match at cosine 0.578, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | transportation-autonomous_vehicles<->transport_impact-autonomous_vehicles | Grey zone ruled DROP: 'transportation-autonomous_vehicles' and 'transport_impact-autonomous_vehicles' match at cosine 0.722, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | transportation-autonomous_vehicles<->transportation-autonomous_vehicles | Grey zone ruled DROP: 'transportation-autonomous_vehicles' and 'transportation-autonomous_vehicles' match at cosine 0.606, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->AI-productivity_enhancement | Grey zone ruled KEEP: 'ubiquity' and 'AI-productivity_enhancement' match at cosine 0.569, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->impact-technological_advancement | Grey zone ruled DROP: 'ubiquity' and 'impact-technological_advancement' match at cosine 0.773, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | ubiquity<->labor-competitive_advantage | Grey zone ruled KEEP: 'ubiquity' and 'labor-competitive_advantage' match at cosine 0.498, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | user_experience_relaxation<->experience-convenience_of_travel | Grey zone ruled DROP: 'user_experience_relaxation' and 'experience-convenience_of_travel' match at cosine 0.681, between tau_low 0.45 and tau_high 0.80. | 1 |
| M1 | WARN | grey_zone_judged | user_experience_relaxation<->user_experience_relaxation | Grey zone ruled DROP: 'user_experience_relaxation' and 'user_experience_relaxation' match at cosine 0.742, between tau_low 0.45 and tau_high 0.80. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-automation_of_repetitive_tasks' at cosine 0.693, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'AI-multi-use' at cosine 0.681, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-automation_of_repetitive_tasks | Routes JUDGE against 'impact-work_ease' at cosine 0.653, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-complex_problem_solving | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.554, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-creative_capability | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.597, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-daily_life_assistance | Routes JUDGE against 'ai-utility' at cosine 0.717, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-daily_life_assistance | Routes JUDGE against 'ai-utility' at cosine 0.719, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-daily_life_assistance | Routes JUDGE against 'daily_life_assistance' at cosine 0.750, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-disaster_management | Routes JUDGE against 'impact-work_ease' at cosine 0.605, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-divine_connection | Routes JUDGE against 'AI-enhanced-communication' at cosine 0.719, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-economic_efficiency | Routes JUDGE against 'AI-economic_strengthening' at cosine 0.767, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-economic_strengthening | Routes JUDGE against 'impact-technological_advancement' at cosine 0.628, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-efficiency | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.786, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-employment_transformation | Routes JUDGE against 'AI-economic_strengthening' at cosine 0.629, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-enhanced-communication | Routes JUDGE against 'AI-enhanced-communication' at cosine 0.660, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-enhanced-communication | Routes JUDGE against 'AI-sector-focus-digital_marketing' at cosine 0.610, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-entrepreneurial-support | Routes JUDGE against 'AI-perception-central_role' at cosine 0.637, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-facilitated-collaboration | Routes JUDGE against 'AI-impact-immigration' at cosine 0.569, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-global_defence | Routes JUDGE against 'impact-technological_advancement' at cosine 0.521, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-impact-immigration | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.587, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-impact-women_safety | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.615, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-mindset_shift | Routes JUDGE against 'AI-need_for_awareness' at cosine 0.602, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-multi-use | Routes JUDGE against 'AI-multi-use' at cosine 0.698, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-multi-use | Routes JUDGE against 'AI-multi-use' at cosine 0.791, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-multi-use | Routes JUDGE against 'AI-multi-use' at cosine 0.793, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-multi-use | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.701, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-need_for_awareness | Routes JUDGE against 'AI-need_for_awareness' at cosine 0.620, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-need_for_awareness | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.524, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-omnipotence | Routes JUDGE against 'AI-omnipotence' at cosine 0.747, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-omnipotence | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.664, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-perception-central_role | Routes JUDGE against 'AI-perception-central_role' at cosine 0.724, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-perception-central_role | Routes JUDGE against 'AI-positive_outlook' at cosine 0.542, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-personalisation | Routes JUDGE against 'impact-work_ease' at cosine 0.593, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-positive_outlook | Routes JUDGE against 'AI-positive_outlook' at cosine 0.643, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-positive_outlook | Routes JUDGE against 'AI-positive_outlook' at cosine 0.763, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-positive_outlook | Routes JUDGE against 'AI-positive_outlook' at cosine 0.780, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.675, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'daily_life_assistance-problem_resolution' at cosine 0.758, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'economic_impact-productivity_gain' at cosine 0.597, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-productivity_enhancement | Routes JUDGE against 'impact-work_ease' at cosine 0.720, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role-expansion | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.624, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role-human_replacement | Routes JUDGE against 'AI-employment_transformation' at cosine 0.717, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role-human_replacement | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.615, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-role_expansion | Routes JUDGE against 'AI-automation_of_repetitive_tasks' at cosine 0.608, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector-focus-cyber_security | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.460, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector-focus-defence_education | Routes JUDGE against 'AI-daily_life_assistance' at cosine 0.487, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector-focus-digital_marketing | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.506, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector-focus-health | Routes JUDGE against 'AI-sector-focus-defence_education' at cosine 0.720, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-sector_transformation | Routes JUDGE against 'AI-sector-focus-defence_education' at cosine 0.641, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-superintelligence | Routes JUDGE against 'AI-omnipotence' at cosine 0.650, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-threat-to-humanity | Routes JUDGE against 'concern-human_dependency' at cosine 0.655, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'AI-perception-central_role' at cosine 0.577, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.697, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.773, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.783, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.786, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | AI-ubiquity | Routes JUDGE against 'impact-technological_advancement' at cosine 0.664, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | AI-utility | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.747, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | accessibility-assistance_for_disabled | Routes JUDGE against 'utility-work_efficiency' at cosine 0.462, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | accessibility-free_healthcare | Routes JUDGE against 'AI-economic_efficiency' at cosine 0.601, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-dependence-lifestyle | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.588, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-dependence-lifestyle | Routes JUDGE against 'ai-dependence-lifestyle' at cosine 0.740, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-dependence-lifestyle | Routes JUDGE against 'ai-dependence-lifestyle' at cosine 0.770, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | ai-productivity_enhancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.790, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-utility | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.722, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ai-utility | Routes JUDGE against 'ai-utility' at cosine 0.688, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | ai-utility | Routes JUDGE against 'utility-work_efficiency' at cosine 0.660, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | automation_of_repetitive_tasks | Routes JUDGE against 'AI-impact-immigration' at cosine 0.551, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | benefit-reduced_stress | Routes JUDGE against 'benefit-reduced_stress' at cosine 0.658, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | benefit-reduced_stress | Routes JUDGE against 'safety-reduced_accidents' at cosine 0.533, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving | Routes JUDGE against 'AI-complex_problem_solving' at cosine 0.611, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving | Routes JUDGE against 'AI-multi-use' at cosine 0.695, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | complex_problem_solving-advance_analysis | Routes JUDGE against 'complex_problem_solving' at cosine 0.686, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-deepfakes | Routes JUDGE against 'concern-human_dependency' at cosine 0.675, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-ethical_development | Routes JUDGE against 'concern-ethical_development' at cosine 0.694, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-ethical_development | Routes JUDGE against 'concern-privacy_security' at cosine 0.724, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-human_dependency | Routes JUDGE against 'concern-privacy_security' at cosine 0.568, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-misuse | Routes JUDGE against 'negative_impacts-human_subjugation' at cosine 0.773, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | concern-privacy_security | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.548, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance | Routes JUDGE against 'AI-daily_life_assistance' at cosine 0.694, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance | Routes JUDGE against 'AI-daily_life_assistance' at cosine 0.709, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.721, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance | Routes JUDGE against 'ai-utility' at cosine 0.695, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | daily_life_assistance-problem_resolution | Routes JUDGE against 'daily_life_assistance' at cosine 0.785, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency | Routes JUDGE against 'AI-economic_efficiency' at cosine 0.727, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_efficiency | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.677, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_impact-productivity_gain | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.618, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_impact-productivity_gain | Routes JUDGE against 'economic_impact-productivity_gain' at cosine 0.691, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | economic_impact-universal_basic_income | Routes JUDGE against 'impact-technological_advancement' at cosine 0.507, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | education-literacy_requirement | Routes JUDGE against 'AI-need_for_awareness' at cosine 0.622, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | education-sector-transformation | Routes JUDGE against 'sector-focus-cyber_security' at cosine 0.685, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | employment_transformation | Routes JUDGE against 'sector_transformation' at cosine 0.665, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-communication_enhancement | Routes JUDGE against 'AI-enhanced-communication' at cosine 0.605, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-communication_enhancement | Routes JUDGE against 'AI-enhanced-communication' at cosine 0.759, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-communication_enhancement | Routes JUDGE against 'AI-impact-women_safety' at cosine 0.494, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-digital_exclusion | Routes JUDGE against 'labor-job_transformation' at cosine 0.652, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-public_safety | Routes JUDGE against 'AI-economic_efficiency' at cosine 0.618, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-public_safety | Routes JUDGE against 'AI-impact-women_safety' at cosine 0.604, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.710, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.655, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.677, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.697, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.710, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'impact-technological_advancement' at cosine 0.733, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | impact-technological_advancement | Routes JUDGE against 'safety-reduced_accidents' at cosine 0.578, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-work_ease | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.581, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | impact-work_ease | Routes JUDGE against 'impact-work_ease' at cosine 0.779, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | labor-competitive_advantage | Routes JUDGE against 'benefit-reduced_stress' at cosine 0.549, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | labor-competitive_advantage | Routes JUDGE against 'labor-competitive_advantage' at cosine 0.729, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | labor-job_transformation | Routes JUDGE against 'impact-public_safety' at cosine 0.585, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | labor-job_transformation | Routes JUDGE against 'labor-job_transformation' at cosine 0.601, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-cybersecurity_risks | Routes JUDGE against 'AI-sector-focus-cyber_security' at cosine 0.562, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-human_subjugation | Routes JUDGE against 'concern-human_dependency' at cosine 0.796, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.723, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.763, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'concern-human_dependency' at cosine 0.679, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'concern-human_dependency' at cosine 0.717, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'concern-human_dependency' at cosine 0.728, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-human_subjugation' at cosine 0.779, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-job_destruction' at cosine 0.758, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.612, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.629, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-job_destruction | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.692, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-laziness | Routes JUDGE against 'concern-human_dependency' at cosine 0.748, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-laziness | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.538, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-laziness | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.764, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'concern-ethical_development' at cosine 0.703, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.635, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | negative_impacts-misuse | Routes JUDGE against 'negative_impacts-misuse' at cosine 0.709, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | perception-central_role | Routes JUDGE against 'AI-perception-central_role' at cosine 0.769, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | perception-technological_luck | Routes JUDGE against 'AI-positive_outlook' at cosine 0.512, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | personalisation | Routes JUDGE against 'AI-personalisation' at cosine 0.765, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | personalisation | Routes JUDGE against 'personalisation' at cosine 0.664, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | personalisation | Routes JUDGE against 'personalisation' at cosine 0.774, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | personalisation-virtual_trials | Routes JUDGE against 'personalisation' at cosine 0.670, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outcomes-work_relief | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.638, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outcomes-work_relief | Routes JUDGE against 'positive_outcomes-work_relief' at cosine 0.708, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'AI-enhanced-communication' at cosine 0.708, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.727, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | positive_outlook | Routes JUDGE against 'positive_outlook' at cosine 0.747, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | safety-improvements-shelter_security | Routes JUDGE against 'safety_improvements' at cosine 0.625, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | safety-reduced_accidents | Routes JUDGE against 'AI-impact-women_safety' at cosine 0.571, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | safety_improvements | Routes JUDGE against 'safety-reduced_accidents' at cosine 0.560, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-cyber_security | Routes JUDGE against 'AI-sector-focus-cyber_security' at cosine 0.707, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-digital_marketing | Routes JUDGE against 'AI-sector-focus-defence_education' at cosine 0.746, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector-focus-transportation | Routes JUDGE against 'AI-sector_transformation' at cosine 0.706, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | sector_transformation | Routes JUDGE against 'labor-job_transformation' at cosine 0.651, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | society-digital-transformation | Routes JUDGE against 'AI-impact-women_safety' at cosine 0.512, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | society-digital-transformation | Routes JUDGE against 'society-digital-transformation' at cosine 0.689, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | transport_automation | Routes JUDGE against 'transportation-autonomous_vehicles' at cosine 0.594, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'AI-productivity_enhancement' at cosine 0.508, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'AI-role-human_replacement' at cosine 0.696, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-autonomous_vehicles | Routes JUDGE against 'sector-focus-cyber_security' at cosine 0.684, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | transportation-navigation_assistance | Routes JUDGE against 'accessibility-assistance_for_disabled' at cosine 0.649, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.649, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.681, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | ubiquity | Routes JUDGE against 'AI-ubiquity' at cosine 0.792, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | user_experience_relaxation | Routes JUDGE against 'user_experience_relaxation' at cosine 0.670, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | user_experience_relaxation | Routes JUDGE against 'utility-work_efficiency' at cosine 0.460, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | utility-efficiency_gain | Routes JUDGE against 'utility-work_efficiency' at cosine 0.769, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M2 | WARN | route_judge | utility-work_efficiency | Routes JUDGE against 'AI-economic_efficiency' at cosine 0.709, in the grey zone [0.45, 0.80); the judge ruled CREATE. | 1 |
| M2 | WARN | route_judge | utility-work_efficiency | Routes JUDGE against 'utility-work_efficiency' at cosine 0.775, in the grey zone [0.45, 0.80); the judge ruled MERGE. | 1 |
| M3 | WARN | fit_incomplete | AI-automation_of_repetitive_tasks | Judge ruled INCOMPLETE on 'AI-automation_of_repetitive_tasks' in response 81 (fit 0.253 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | economic_impact | Judge ruled INCOMPLETE on 'economic_impact' in response 94 (fit 0.262 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | impact-technological_advancement | Judge ruled INCOMPLETE on 'impact-technological_advancement' in response 77 (fit 0.294 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | positive_outlook | Judge ruled INCOMPLETE on 'positive_outlook' in response 52 (fit 0.289 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| M3 | WARN | fit_incomplete | positive_outlook | Judge ruled INCOMPLETE on 'positive_outlook' in response 94 (fit 0.289 < tau_fit 0.30): the code did not describe this response segment completely; kept and flagged for the slow loop, with no replacement code invented. | 1 |
| S1 | ERROR | missing_evidence | impact-women_safety | Candidate cites no evidence, so it cannot be traced back to the corpus. | 1 |
| S2 | ERROR | no_verified_evidence | AI-ubiquity | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 1 |
| S2 | ERROR | no_verified_evidence | personalisation | No quote could be verified against the response, so the candidate has no evidence left to stand on. | 1 |
| S2b | WARN | quote_too_long | AI-productivity_enhancement | Quote spans 3 sentences; coding should be applied at the level of phrase or sentence (at most 2). | 2 |
| S2b | WARN | quote_too_long | automation_of_repetitive_tasks | Quote spans 3 sentences; coding should be applied at the level of phrase or sentence (at most 2). | 1 |
| S2b | WARN | quote_too_long | transportation-autonomous_vehicles | Quote spans 3 sentences; coding should be applied at the level of phrase or sentence (at most 2). | 1 |
| S3 | WARN | sub_code_first | complex_problem_solving | The family 'complex_problem_solving' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 2 |
| S3 | WARN | sub_code_first | daily_life_assistance | The family 'daily_life_assistance' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 2 |
| S3 | WARN | sub_code_first | economic_efficiency | The family 'economic_efficiency' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 1 |
| S3 | WARN | sub_code_first | economic_impact | The family 'economic_impact' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 1 |
| S3 | WARN | sub_code_first | personalisation | The family 'personalisation' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 3 |
| S3 | WARN | sub_code_first | positive_outlook | The family 'positive_outlook' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 14 |
| S3 | WARN | sub_code_first | sector_transformation | The family 'sector_transformation' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 1 |
| S3 | WARN | sub_code_first | user_experience_relaxation | The family 'user_experience_relaxation' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 2 |
| S3 | WARN | sub_code_first | utility | The family 'utility' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 1 |
| S5 | WARN | too_few_codes | 44 | Coder 'coder_a' produced 1 codes for this response, fewer than the usual 2 to 12. | 1 |
| S6 | ERROR | duplicate_name | AI-productivity_enhancement | 2 codes share the name 'AI-productivity_enhancement' (case-insensitively), so a name no longer identifies a code. | 1 |
| S6 | ERROR | duplicate_name | AI-utility | 2 codes share the name 'AI-utility' (case-insensitively), so a name no longer identifies a code. | 1 |

## Pipeline counts

| quantity | value |
|---|---|
| candidates proposed (coder A / B) | 185 / 213 |
| candidates accepted | 274 |
| dropped: structural / fit / dispute | 3 / 0 / 65 |
| routes CREATE / MERGE / JUDGE | 8 / 104 / 162 |
| coder agreement rate | 0.232 |
| model calls (all mock) | 369 |
| checkpoint due | True (new codes this batch 16 > 8) |
| snapshots | snap-8c8e1bb384bd3da4, snap-d4e4b2009ff45f94, snap-b8844b2f6c80cee9, snap-dca97b7821f0bff4, snap-94604cbe2e263327 |

## The machine codebook (names and descriptions; the quotes stay in the run directory)

| code | parent | description | evidence | assignments | created in |
|---|---|---|---:|---:|---|
| `AI-automation_of_repetitive_tasks` | - | *definition withheld: shares wording with a response* | 7 | 7 | snap-8c8e1bb384bd3da4 |
| `AI-complex_problem_solving` | - | The view that AI capabilities include smarter decision-making and the ability to solve complex problems. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-creative_capability` | - | The respondent associates AI with the ability to perform creative acts like altering faces and voices. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-daily_life_assistance` | - | The respondent cites specific examples of AI tools like Siri and Alexa being useful in day-to-day life. | 5 | 5 | snap-8c8e1bb384bd3da4 |
| `AI-disaster_management` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-divine_connection` | - | The respondent envisions a scenario where AI enables communication with deities. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-economic_efficiency` | - | *definition withheld: shares wording with a response* | 4 | 4 | snap-8c8e1bb384bd3da4 |
| `AI-economic_strengthening` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-employment_transformation` | - | The view that AI will fundamentally alter the labor market by creating new opportunities rather than just replacing jobs. | 7 | 7 | snap-8c8e1bb384bd3da4 |
| `AI-enhanced-communication` | - | The respondent envisions AI improving the ability to connect, share information, and build relationships in a digital society. | 6 | 6 | snap-8c8e1bb384bd3da4 |
| `AI-entrepreneurial-support` | - | The respondent believes AI will provide specific tools that aid in developing organizations and fostering entrepreneurship. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-facilitated-collaboration` | - | The scenario describes AI enabling people to work together effectively towards common goals across distances. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-global_defence` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-impact-immigration` | - | The respondent describes a scenario where AI facilitates fast immigration for foreigners to other countries. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-impact-women_safety` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-mindset_shift` | - | The necessity for individuals and society to adopt a positive mindset towards AI technology. | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `AI-multi-use` | - | *definition withheld: shares wording with a response* | 11 | 11 | snap-8c8e1bb384bd3da4 |
| `AI-need_for_awareness` | - | The call for more people to be aware of AI features and uses. | 4 | 4 | snap-8c8e1bb384bd3da4 |
| `AI-omnipotence` | - | The respondent describes AI as having the ability to handle any task or product quality uniquely. | 5 | 5 | snap-8c8e1bb384bd3da4 |
| `AI-perception-central_role` | - | *definition withheld: shares wording with a response* | 5 | 5 | snap-8c8e1bb384bd3da4 |
| `AI-personalisation` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-positive_outlook` | - | *definition withheld: shares wording with a response* | 8 | 8 | snap-8c8e1bb384bd3da4 |
| `AI-productivity_enhancement` | - | *definition withheld: shares wording with a response* | 18 | 18 | snap-8c8e1bb384bd3da4 |
| `AI-role-expansion` | - | The respondent lists specific diverse functions AI will assume, such as servant, teacher, businessman, or spy. | 3 | 3 | snap-8c8e1bb384bd3da4 |
| `AI-role-human_replacement` | - | The respondent envisions a future where AI performs all technological work while human labor diminishes. | 10 | 10 | snap-8c8e1bb384bd3da4 |
| `AI-role_expansion` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-dca97b7821f0bff4 |
| `AI-sector-focus-cyber_security` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-sector-focus-defence_education` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-sector-focus-digital_marketing` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `AI-sector-focus-health` | - | The respondent identifies the healthcare sector as a primary area where AI will provide free, accessible solutions and improve human health. | 2 | 2 | snap-dca97b7821f0bff4 |
| `AI-sector_transformation` | - | The expectation that AI will influence specific fields such as education, infrastructure (roadways, railways), and defence. | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `AI-superintelligence` | - | The respondent describes the transition of AI into a superintelligent state that surpasses human capability. | 2 | 2 | snap-b8844b2f6c80cee9 |
| `AI-threat-to-humanity` | - | The perception of AI as a direct existential threat to human existence. | 1 | 1 | snap-dca97b7821f0bff4 |
| `AI-ubiquity` | - | The respondent perceives AI as being widely adopted and integrated into daily life globally. | 14 | 14 | snap-8c8e1bb384bd3da4 |
| `AI-utility` | - | The respondent describes AI acting as a helpful assistant to perform tasks like research and decision-making for the user. | 1 | 1 | snap-dca97b7821f0bff4 |
| `accessibility-assistance_for_disabled` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `accessibility-free_healthcare` | - | The belief that AI will provide medical solutions and answers without financial costs to the user. | 1 | 1 | snap-dca97b7821f0bff4 |
| `ai-dependence-lifestyle` | - | The belief that society will become increasingly reliant on AI for daily tasks and living, potentially leading to a decline in human effort or initiative. | 13 | 13 | snap-8c8e1bb384bd3da4 |
| `ai-productivity_enhancement` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-dca97b7821f0bff4 |
| `ai-utility` | - | The role of AI as a helpful assistant in various contexts. | 8 | 8 | snap-8c8e1bb384bd3da4 |
| `automation_of_repetitive_tasks` | - | The respondent describes a scenario where booking a ticket is handled automatically by the system. | 1 | 1 | snap-d4e4b2009ff45f94 |
| `benefit-reduced_stress` | - | The positive outcome of reduced workplace stress due to AI integration. | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `complex_problem_solving` | - | *definition withheld: shares wording with a response* | 3 | 3 | snap-b8844b2f6c80cee9 |
| `complex_problem_solving-advance_analysis` | `complex_problem_solving` | *definition withheld: shares wording with a response* | 1 | 1 | snap-dca97b7821f0bff4 |
| `concern-deepfakes` | - | The specific worry regarding the proliferation of AI-generated fake media. | 1 | 1 | snap-b8844b2f6c80cee9 |
| `concern-ethical_development` | - | The respondent expresses concern about the safety and responsible development of AI systems. | 3 | 3 | snap-b8844b2f6c80cee9 |
| `concern-human_dependency` | - | *definition withheld: shares wording with a response* | 12 | 12 | snap-8c8e1bb384bd3da4 |
| `concern-misuse` | - | *definition withheld: shares wording with a response* | 2 | 2 | snap-dca97b7821f0bff4 |
| `concern-privacy_security` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `daily_life_assistance` | - | *definition withheld: shares wording with a response* | 5 | 5 | snap-b8844b2f6c80cee9 |
| `daily_life_assistance-problem_resolution` | `daily_life_assistance` | The respondent views AI as a tool that assists in resolving personal problems and improving living conditions. | 1 | 1 | snap-dca97b7821f0bff4 |
| `economic_efficiency` | - | *definition withheld: shares wording with a response* | 2 | 2 | snap-b8844b2f6c80cee9 |
| `economic_impact-productivity_gain` | - | The use of AI to increase the speed and volume of output. | 5 | 5 | snap-8c8e1bb384bd3da4 |
| `economic_impact-universal_basic_income` | - | The proposal of a state-provided income to support people whose jobs have been automated. | 1 | 1 | snap-d4e4b2009ff45f94 |
| `education-literacy_requirement` | - | *definition withheld: shares wording with a response* | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `education-sector-transformation` | - | *definition withheld: shares wording with a response* | 2 | 2 | snap-b8844b2f6c80cee9 |
| `employment_transformation` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-dca97b7821f0bff4 |
| `impact-communication_enhancement` | - | *definition withheld: shares wording with a response* | 3 | 3 | snap-8c8e1bb384bd3da4 |
| `impact-digital_connectivity` | - | The ability of digital platforms to connect people and build relationships globally. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `impact-digital_exclusion` | - | The risk of AI systems cutting off human access to digital infrastructure. | 1 | 1 | snap-dca97b7821f0bff4 |
| `impact-public_safety` | - | *definition withheld: shares wording with a response* | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `impact-technological_advancement` | - | The belief that AI will lead to overall progress in various aspects of life. | 10 | 10 | snap-8c8e1bb384bd3da4 |
| `impact-work_ease` | - | The perception that AI will make professional tasks easier to perform. | 6 | 6 | snap-8c8e1bb384bd3da4 |
| `labor-competitive_advantage` | - | The benefit gained by individuals who adopt AI technologies compared to those who do not. | 3 | 3 | snap-8c8e1bb384bd3da4 |
| `labor-job_transformation` | - | The significant effect of AI on the nature and availability of human work. | 5 | 5 | snap-8c8e1bb384bd3da4 |
| `negative_impacts-cybersecurity_risks` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `negative_impacts-human_subjugation` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-dca97b7821f0bff4 |
| `negative_impacts-job_destruction` | - | The respondent identifies the loss of employment for human drivers as a specific negative societal impact. | 11 | 11 | snap-8c8e1bb384bd3da4 |
| `negative_impacts-laziness` | - | *definition withheld: shares wording with a response* | 8 | 8 | snap-8c8e1bb384bd3da4 |
| `negative_impacts-misuse` | - | *definition withheld: shares wording with a response* | 9 | 9 | snap-8c8e1bb384bd3da4 |
| `perception-technological_luck` | - | The view that discovering AI technology is a fortunate occurrence for humanity. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `personalisation` | - | The ability of AI to tailor experiences or recommendations based on individual user preferences. | 3 | 3 | snap-b8844b2f6c80cee9 |
| `personalisation-virtual_trials` | `personalisation` | The use of AI to virtually test or trial products before making a purchase. | 1 | 1 | snap-dca97b7821f0bff4 |
| `positive_outcomes-work_relief` | - | The view that AI advancements offer significant benefits by reducing job stress and making work easier for people. | 7 | 7 | snap-8c8e1bb384bd3da4 |
| `positive_outlook` | - | *definition withheld: shares wording with a response* | 14 | 14 | snap-d4e4b2009ff45f94 |
| `resource-efficiency` | - | The conservation of resources through technological implementation. | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `safety-improvements-shelter_security` | - | The enhancement of safety protocols within residential or care facilities. | 1 | 1 | snap-d4e4b2009ff45f94 |
| `safety-reduced_accidents` | - | AI technology is expected to significantly reduce accidents and save human lives. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `safety_improvements` | - | The reduction of accidents and hazards in public spaces. | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `sector-focus-cyber_security` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-b8844b2f6c80cee9 |
| `sector-focus-digital_marketing` | - | The respondent identifies a specific sector or function where AI will play a major role. | 1 | 1 | snap-dca97b7821f0bff4 |
| `sector-focus-transportation` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-dca97b7821f0bff4 |
| `sector_transformation` | - | The respondent describes a fundamental change in how an industry operates due to AI. | 2 | 2 | snap-d4e4b2009ff45f94 |
| `security-cyber_security` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `society-digital-transformation` | - | *definition withheld: shares wording with a response* | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `transport_automation` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-8c8e1bb384bd3da4 |
| `transportation-autonomous_vehicles` | - | AI enables self-driving cars that improve safety, conserve resources, and assist those unable to drive. | 4 | 4 | snap-8c8e1bb384bd3da4 |
| `transportation-navigation_assistance` | - | AI provides guidance and route planning for travelers. | 1 | 1 | snap-d4e4b2009ff45f94 |
| `ubiquity` | - | *definition withheld: shares wording with a response* | 1 | 1 | snap-dca97b7821f0bff4 |
| `user_experience_relaxation` | - | *definition withheld: shares wording with a response* | 2 | 2 | snap-8c8e1bb384bd3da4 |
| `utility-work_efficiency` | - | AI tools that help users complete tasks faster and meet deadlines. | 6 | 6 | snap-8c8e1bb384bd3da4 |
