# 11 - Pattern mapping: which responses look alike

A pattern group is a set of responses that touch exactly the same families. It is a
description of the coding, not a claim about the respondents: two responses in one
group may say opposite things about the same subjects.

## Patterns in the machine run

200 responses x 162 codes; minimum support 2.
3 pattern group(s) — responses touching exactly the same set of
families — and 193 response(s) whose family signature is unique.

| size | families touched | responses |
|---:|---|---|
| 2 | `AI`, `creative_capability`, `daily_life_assistance`, `multi`, `positive_outlook` | 555, 586 |
| 2 | `AI`, `impact` | 33, 43 |
| 2 | `AI`, `impact`, `positive_outlook`, `society` | 186, 304 |

### Family co-occurrence (responses carrying both)

| family | AI | accessibility | ai | automation_of_repetitive_tasks | benefit | complex_problem_solving | concern | creative_capability | daily_life_assistance | deepfakes | dependence | economic_efficiency | economic_impact | education | employment_transformation | enhanced | facilitated | global_defence | impact | job_displacement | labor | mindset_shift | multi | multi_use | need_for_awareness | negative_impacts | perception | personalisation | positive_outcomes | positive_outlook | privacy_security | resource | robotics_engineering | role_human_replacement | safety | safety_improvements | sector | sector_transformation | security | society | threat | transport_automation | transportation | ubiquity | unclear_outputs | user_experience_relaxation | utility | workforce_retraining |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `AI` | 176 | 3 | 38 | 3 | 3 | 19 | 27 | 10 | 35 | 1 | 2 | 28 | 10 | 18 | 32 | 0 | 1 | 1 | 76 | 15 | 9 | 4 | 12 | 2 | 15 | 60 | 5 | 16 | 30 | 82 | 7 | 1 | 1 | 1 | 11 | 0 | 32 | 6 | 1 | 10 | 9 | 0 | 11 | 46 | 1 | 1 | 38 | 1 |
| `accessibility` | 3 | 5 | 1 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 3 | 0 | 1 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 1 | 0 | 1 | 0 | 0 |
| `ai` | 38 | 1 | 47 | 0 | 1 | 3 | 12 | 2 | 5 | 0 | 0 | 3 | 3 | 4 | 4 | 0 | 0 | 1 | 19 | 5 | 3 | 1 | 1 | 0 | 7 | 23 | 2 | 5 | 8 | 21 | 0 | 0 | 1 | 0 | 0 | 0 | 6 | 0 | 0 | 1 | 8 | 0 | 4 | 11 | 0 | 1 | 8 | 0 |
| `automation_of_repetitive_tasks` | 3 | 0 | 0 | 3 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 2 | 0 | 0 | 0 | 0 |
| `benefit` | 3 | 0 | 1 | 0 | 4 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 2 | 2 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 1 | 0 |
| `complex_problem_solving` | 19 | 1 | 3 | 1 | 1 | 20 | 2 | 2 | 5 | 1 | 1 | 1 | 1 | 2 | 4 | 0 | 0 | 0 | 10 | 1 | 0 | 1 | 1 | 1 | 1 | 4 | 0 | 3 | 4 | 11 | 2 | 0 | 0 | 1 | 1 | 0 | 6 | 2 | 0 | 0 | 0 | 0 | 0 | 8 | 0 | 0 | 4 | 0 |
| `concern` | 27 | 0 | 12 | 0 | 1 | 2 | 33 | 1 | 2 | 1 | 0 | 2 | 0 | 3 | 1 | 0 | 0 | 0 | 10 | 4 | 0 | 1 | 0 | 0 | 5 | 25 | 1 | 0 | 4 | 9 | 1 | 0 | 0 | 0 | 2 | 1 | 8 | 1 | 0 | 1 | 5 | 1 | 2 | 8 | 0 | 0 | 6 | 0 |
| `creative_capability` | 10 | 0 | 2 | 0 | 1 | 2 | 1 | 10 | 6 | 1 | 0 | 2 | 1 | 1 | 1 | 0 | 0 | 0 | 2 | 2 | 0 | 0 | 4 | 0 | 0 | 1 | 0 | 0 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 2 | 0 |
| `daily_life_assistance` | 35 | 1 | 5 | 0 | 1 | 5 | 2 | 6 | 38 | 1 | 2 | 7 | 0 | 3 | 5 | 1 | 1 | 1 | 10 | 1 | 1 | 1 | 7 | 1 | 0 | 8 | 1 | 3 | 8 | 23 | 2 | 0 | 1 | 0 | 2 | 0 | 7 | 1 | 0 | 3 | 0 | 0 | 2 | 10 | 0 | 0 | 10 | 0 |
| `deepfakes` | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| `dependence` | 2 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| `economic_efficiency` | 28 | 0 | 3 | 1 | 1 | 1 | 2 | 2 | 7 | 0 | 0 | 31 | 2 | 2 | 10 | 0 | 1 | 1 | 12 | 5 | 1 | 1 | 1 | 1 | 4 | 5 | 0 | 3 | 6 | 19 | 4 | 0 | 0 | 0 | 3 | 0 | 8 | 2 | 0 | 1 | 2 | 0 | 3 | 8 | 0 | 0 | 7 | 0 |
| `economic_impact` | 10 | 0 | 3 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 2 | 10 | 2 | 1 | 0 | 0 | 0 | 5 | 0 | 4 | 0 | 0 | 0 | 0 | 3 | 0 | 1 | 2 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| `education` | 18 | 1 | 4 | 0 | 0 | 2 | 3 | 1 | 3 | 0 | 0 | 2 | 2 | 21 | 2 | 1 | 0 | 0 | 7 | 0 | 2 | 0 | 2 | 0 | 1 | 5 | 1 | 3 | 2 | 11 | 0 | 1 | 1 | 0 | 2 | 0 | 7 | 0 | 0 | 1 | 0 | 0 | 1 | 3 | 0 | 0 | 5 | 0 |
| `employment_transformation` | 32 | 1 | 4 | 1 | 0 | 4 | 1 | 1 | 5 | 0 | 0 | 10 | 1 | 2 | 37 | 0 | 0 | 0 | 16 | 4 | 0 | 0 | 3 | 1 | 3 | 11 | 2 | 3 | 6 | 18 | 4 | 0 | 0 | 1 | 2 | 0 | 8 | 3 | 0 | 2 | 0 | 0 | 3 | 12 | 0 | 0 | 9 | 1 |
| `enhanced` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| `facilitated` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| `global_defence` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| `impact` | 76 | 3 | 19 | 2 | 2 | 10 | 10 | 2 | 10 | 0 | 0 | 12 | 5 | 7 | 16 | 1 | 0 | 1 | 84 | 6 | 3 | 2 | 4 | 1 | 4 | 26 | 3 | 8 | 16 | 44 | 1 | 1 | 1 | 1 | 5 | 0 | 16 | 2 | 0 | 5 | 1 | 0 | 6 | 18 | 0 | 1 | 21 | 0 |
| `job_displacement` | 15 | 0 | 5 | 0 | 0 | 1 | 4 | 2 | 1 | 1 | 0 | 5 | 0 | 0 | 4 | 0 | 0 | 0 | 6 | 18 | 0 | 0 | 2 | 0 | 4 | 10 | 0 | 0 | 3 | 4 | 3 | 0 | 0 | 0 | 1 | 0 | 4 | 2 | 0 | 0 | 4 | 0 | 4 | 3 | 0 | 0 | 2 | 0 |
| `labor` | 9 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 4 | 2 | 0 | 0 | 0 | 0 | 3 | 0 | 9 | 0 | 1 | 0 | 0 | 4 | 0 | 0 | 3 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| `mindset_shift` | 4 | 0 | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 5 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 1 | 0 | 1 | 0 |
| `multi` | 12 | 0 | 1 | 0 | 0 | 1 | 0 | 4 | 7 | 0 | 0 | 1 | 0 | 2 | 3 | 0 | 0 | 0 | 4 | 2 | 1 | 0 | 14 | 0 | 1 | 2 | 0 | 1 | 2 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 4 | 0 |
| `multi_use` | 2 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| `need_for_awareness` | 15 | 0 | 7 | 1 | 0 | 1 | 5 | 0 | 0 | 0 | 0 | 4 | 0 | 1 | 3 | 0 | 0 | 0 | 4 | 4 | 0 | 0 | 1 | 0 | 19 | 10 | 0 | 1 | 1 | 8 | 2 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 0 | 0 | 4 | 0 | 0 | 6 | 0 | 0 | 3 | 0 |
| `negative_impacts` | 60 | 0 | 23 | 0 | 1 | 4 | 25 | 1 | 8 | 1 | 0 | 5 | 3 | 5 | 11 | 0 | 0 | 1 | 26 | 10 | 4 | 1 | 2 | 0 | 10 | 71 | 1 | 2 | 8 | 23 | 2 | 0 | 0 | 0 | 3 | 1 | 12 | 3 | 0 | 4 | 10 | 1 | 7 | 15 | 1 | 0 | 10 | 0 |
| `perception` | 5 | 0 | 2 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 2 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 6 | 0 | 3 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 1 |
| `personalisation` | 16 | 1 | 5 | 1 | 0 | 3 | 0 | 0 | 3 | 0 | 0 | 3 | 1 | 3 | 3 | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 1 | 0 | 1 | 2 | 0 | 17 | 3 | 7 | 1 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 3 | 2 | 0 | 1 | 2 | 0 |
| `positive_outcomes` | 30 | 0 | 8 | 0 | 2 | 4 | 4 | 3 | 8 | 0 | 0 | 6 | 2 | 2 | 6 | 0 | 0 | 0 | 16 | 3 | 3 | 0 | 2 | 2 | 1 | 8 | 3 | 3 | 32 | 10 | 3 | 0 | 0 | 1 | 1 | 0 | 5 | 1 | 0 | 2 | 2 | 0 | 0 | 6 | 0 | 1 | 9 | 1 |
| `positive_outlook` | 82 | 3 | 21 | 3 | 2 | 11 | 9 | 3 | 23 | 0 | 2 | 19 | 3 | 11 | 18 | 0 | 1 | 2 | 44 | 4 | 4 | 3 | 8 | 1 | 8 | 23 | 2 | 7 | 10 | 94 | 4 | 1 | 1 | 0 | 9 | 0 | 17 | 3 | 0 | 5 | 2 | 0 | 9 | 29 | 0 | 0 | 23 | 0 |
| `privacy_security` | 7 | 0 | 0 | 1 | 0 | 2 | 1 | 0 | 2 | 0 | 1 | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 1 | 3 | 0 | 1 | 0 | 0 | 2 | 2 | 0 | 1 | 3 | 4 | 9 | 0 | 0 | 0 | 0 | 0 | 3 | 1 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 0 | 1 | 0 |
| `resource` | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 |
| `robotics_engineering` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 2 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 2 | 0 |
| `role_human_replacement` | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| `safety` | 11 | 3 | 0 | 0 | 1 | 1 | 2 | 0 | 2 | 0 | 0 | 3 | 0 | 2 | 2 | 0 | 1 | 0 | 5 | 1 | 0 | 0 | 0 | 0 | 1 | 3 | 0 | 0 | 1 | 9 | 0 | 1 | 0 | 0 | 14 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 6 | 5 | 0 | 1 | 3 | 0 |
| `safety_improvements` | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| `sector` | 32 | 0 | 6 | 1 | 1 | 6 | 8 | 2 | 7 | 1 | 0 | 8 | 0 | 7 | 8 | 1 | 0 | 1 | 16 | 4 | 0 | 1 | 3 | 1 | 1 | 12 | 0 | 4 | 5 | 17 | 3 | 0 | 1 | 1 | 2 | 0 | 37 | 4 | 0 | 0 | 0 | 0 | 4 | 12 | 0 | 1 | 6 | 0 |
| `sector_transformation` | 6 | 0 | 0 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 0 | 2 | 0 | 0 | 3 | 0 | 0 | 0 | 2 | 2 | 1 | 0 | 0 | 1 | 1 | 3 | 0 | 0 | 1 | 3 | 1 | 0 | 0 | 1 | 0 | 0 | 4 | 6 | 0 | 0 | 0 | 0 | 2 | 3 | 0 | 0 | 0 | 0 |
| `security` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `society` | 10 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 3 | 0 | 0 | 1 | 0 | 1 | 2 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 2 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 2 | 0 | 0 | 2 | 0 |
| `threat` | 9 | 0 | 8 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 4 | 0 | 0 | 0 | 0 | 4 | 10 | 0 | 0 | 2 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 0 | 0 | 3 | 1 | 0 | 1 | 0 |
| `transport_automation` | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| `transportation` | 11 | 3 | 4 | 1 | 0 | 0 | 2 | 0 | 2 | 0 | 0 | 3 | 0 | 1 | 3 | 0 | 0 | 1 | 6 | 4 | 1 | 0 | 0 | 0 | 0 | 7 | 0 | 3 | 0 | 9 | 0 | 1 | 0 | 0 | 6 | 0 | 4 | 2 | 0 | 0 | 0 | 0 | 17 | 3 | 0 | 1 | 1 | 0 |
| `ubiquity` | 46 | 1 | 11 | 2 | 2 | 8 | 8 | 2 | 10 | 1 | 1 | 8 | 0 | 3 | 12 | 0 | 1 | 0 | 18 | 3 | 0 | 4 | 4 | 1 | 6 | 15 | 0 | 2 | 6 | 29 | 1 | 0 | 1 | 1 | 5 | 0 | 12 | 3 | 0 | 2 | 3 | 0 | 3 | 49 | 1 | 0 | 18 | 0 |
| `unclear_outputs` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 2 | 0 | 0 | 0 |
| `user_experience_relaxation` | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 2 | 0 | 0 |
| `utility` | 38 | 0 | 8 | 0 | 1 | 4 | 6 | 2 | 10 | 0 | 0 | 7 | 2 | 5 | 9 | 1 | 0 | 0 | 21 | 2 | 0 | 1 | 4 | 0 | 3 | 10 | 6 | 2 | 9 | 23 | 1 | 0 | 2 | 0 | 3 | 0 | 6 | 0 | 0 | 2 | 1 | 0 | 1 | 18 | 0 | 0 | 46 | 1 |
| `workforce_retraining` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |

### Code pairs that travel together (783 at or above support 2)

`lift` is the joint share over the product of the two individual shares: 1.0 is
chance, above 1.0 is more often than chance.

| code | code | support | share | lift |
|---|---|---:|---:|---:|
| `AI-productivity_enhancement` | `positive_outlook` | 34 | 0.170 | 1.002 |
| `impact-technological_advancement` | `positive_outlook` | 32 | 0.160 | 1.338 |
| `positive_outlook` | `ubiquity` | 28 | 0.140 | 1.314 |
| `AI-productivity_enhancement` | `AI-utility` | 27 | 0.135 | 1.573 |
| `AI-utility` | `positive_outlook` | 23 | 0.115 | 1.202 |
| `AI-productivity_enhancement` | `positive_outcomes-work_relief` | 21 | 0.105 | 1.857 |
| `AI-productivity_enhancement` | `ubiquity` | 20 | 0.100 | 1.047 |
| `AI-productivity_enhancement` | `impact-technological_advancement` | 19 | 0.095 | 0.886 |
| `AI-productivity_enhancement` | `AI-role-human_replacement` | 16 | 0.080 | 1.323 |
| `ubiquity` | `utility-work_ease` | 14 | 0.070 | 2.041 |
| `daily_life_assistance-problem_resolution` | `positive_outlook` | 13 | 0.065 | 1.423 |
| `AI-automation_of_repetitive_tasks` | `AI-productivity_enhancement` | 13 | 0.065 | 1.389 |
| `AI-productivity_enhancement` | `utility-work_ease` | 13 | 0.065 | 1.190 |
| `AI-utility` | `impact-technological_advancement` | 13 | 0.065 | 1.074 |
| `positive_outlook` | `utility-work_ease` | 13 | 0.065 | 1.067 |
| `AI-utility` | `daily_life_assistance-problem_resolution` | 12 | 0.060 | 2.597 |
| `AI-role-human_replacement` | `ubiquity` | 12 | 0.060 | 1.580 |
| `AI-multi-use` | `AI-productivity_enhancement` | 12 | 0.060 | 1.231 |
| `AI-multi-use` | `positive_outlook` | 12 | 0.060 | 1.103 |
| `ai-dependence-lifestyle` | `positive_outlook` | 12 | 0.060 | 0.951 |

Triples at or above the same support: 828.
