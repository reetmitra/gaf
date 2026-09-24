# 13 - Crosswalk: the machine's codebook mapped onto his

Space `lexical-v1-512`; tau_high 0.8, tau_low 0.45;
names only: no.
22 machine leaves against 117 of his.

> Compared as name + description on both sides (every leaf on both sides carries one); no fairness gap.

| band | machine leaves | what it means |
|---|---:|---|
| `same` | 0 | at or above tau_high 0.8 — the same concept |
| `grey` | 9 | between the thresholds — a live pipeline would ask the judge |
| `unmapped` | 13 | below tau_low 0.45 — nothing of his is close |

**Blind spots: 109 of his leaves nothing maps onto.**
**Inventions: 13 machine leaves with no counterpart of his.**

## Every machine leaf

`hungarian` is the one-to-one assignment over the whole vocabulary; `nearest` is the
unconstrained neighbour. They differ when a better-scoring leaf took the target first.

| machine leaf | hungarian target | score | band | nearest target | score | band |
|---|---|---:|---|---|---:|---|
| `adoption-everyday_life` | `adoption-high` | 0.456 | grey | `ease-life` | 0.470 | grey |
| `adoption-social_change` | - | - | - | `adoption-necessity` | 0.286 | unmapped |
| `applications-automation` | - | - | - | `positive_impacts-automation` | 0.338 | unmapped |
| `applications-data_driven_systems` | - | - | - | `positive_impacts-personalisation` | 0.228 | unmapped |
| `applications-education` | `improvement-teaching_learning` | 0.466 | grey | `improvement-teaching_learning` | 0.466 | grey |
| `applications-healthcare` | - | - | - | `applications-medical_care` | 0.420 | unmapped |
| `applications-industry_and_transport` | - | - | - | `key_sectors-transport` | 0.361 | unmapped |
| `applications-personalisation` | `positive_impacts-personalisation` | 0.455 | grey | `positive_impacts-personalisation` | 0.455 | grey |
| `future-imagined_scenario` | - | - | - | `future-inevitability` | 0.156 | unmapped |
| `future-inevitability` | - | - | - | `future-inevitability` | 0.429 | unmapped |
| `future-superintelligence` | - | - | - | `AI-surveillance` | 0.396 | unmapped |
| `future-uncertainty` | - | - | - | `future-inevitability` | 0.396 | unmapped |
| `governance-responsible_development` | - | - | - | `requirements-oversight` | 0.334 | unmapped |
| `negative_impacts-dependence` | - | - | - | `negative_impacts-laziness` | 0.402 | unmapped |
| `negative_impacts-inequality` | - | - | - | `negative_impacts-laziness` | 0.381 | unmapped |
| `negative_impacts-job_loss` | `negative_impacts-job_destruction` | 0.499 | grey | `negative_impacts-job_destruction` | 0.499 | grey |
| `negative_impacts-surveillance` | `negative_impacts-misuse` | 0.503 | grey | `negative_impacts-misuse` | 0.503 | grey |
| `negative_impacts-unskilled_workers` | - | - | - | `impact-context-specific` | 0.275 | unmapped |
| `positive_impacts-access` | `positive_impacts-accessibility` | 0.503 | grey | `positive_impacts-accessibility` | 0.503 | grey |
| `positive_impacts-job_creation` | `positive_impacts-jobs` | 0.458 | grey | `positive_impacts-jobs` | 0.458 | grey |
| `positive_impacts-problem_solving` | `positive_impacts-problem-solving` | 0.475 | grey | `positive_impacts-problem-solving` | 0.475 | grey |
| `positive_impacts-quality_of_life` | `ease-life` | 0.470 | grey | `ease-life` | 0.470 | grey |

## His families, and where the machine's leaves land

| his family | his leaves | machine leaves landing here | from machine families | blind spots |
|---|---:|---:|---|---:|
| `AI` | 8 | 0 | - | 8 |
| `adoption` | 6 | 0 | - | 6 |
| `applications` | 22 | 0 | - | 22 |
| `ease` | 3 | 2 | `adoption` 1, `positive_impacts` 1 | 2 |
| `efficiency` | 1 | 0 | - | 1 |
| `future` | 5 | 0 | - | 5 |
| `impact` | 6 | 0 | - | 6 |
| `improvement` | 8 | 1 | `applications` 1 | 7 |
| `jobs` | 6 | 0 | - | 6 |
| `key_sectors` | 11 | 0 | - | 11 |
| `negative_impacts` | 13 | 2 | `negative_impacts` 2 | 11 |
| `positive_impacts` | 16 | 4 | `applications` 1, `positive_impacts` 3 | 12 |
| `progress` | 3 | 0 | - | 3 |
| `requirements` | 4 | 0 | - | 4 |
| `safety` | 5 | 0 | - | 5 |

## The machine's families, and where they land in his tree

| machine family | leaves | lands in | scattered | unmapped |
|---|---:|---|---|---:|
| `adoption` | 2 | `ease` 1 | no | 1 |
| `applications` | 6 | `improvement` 1, `positive_impacts` 1 | yes | 4 |
| `future` | 4 | - | no | 4 |
| `governance` | 1 | - | no | 1 |
| `negative_impacts` | 5 | `negative_impacts` 2 | no | 3 |
| `positive_impacts` | 4 | `ease` 1, `positive_impacts` 3 | yes | 0 |

### Blind spots — his leaves nothing maps onto

`AI-autonomy`, `AI-machine_communication`, `AI-omnipotence`, `AI-self-modification`, `AI-speed`, `AI-superintelligence`, `AI-surveillance`, `AI-tool`, `adoption-challenges-job_losses`, `adoption-challenges-privacy`, `adoption-challenges-saftey`, `adoption-high`, `adoption-necessity`, `adoption-present`, `applications-chatbots`, `applications-decision-making`, `applications-deep_fakes`, `applications-financial_assistance`, `applications-friend`, `applications-information`, `applications-medical_care`, `applications-meetings`, `applications-navigation`, `applications-personal_assistant`, `applications-planning`, `applications-problem-solving`, `applications-relationships`, `applications-research`, `applications-robotics`, `applications-search`, `applications-self-driving_cars`, `applications-simulation`, `applications-summarising`, `applications-text_generation`, `applications-translation`, `applications-voice_recognition`, `ease-travel`, `ease-work`, `efficiency`, `future-hazard_avoidance`, `future-inevitability`, `future-negative`, `future-positive`, `future-transformation`, `impact-climate_change`, `impact-context-specific`, `impact-global`, `impact-jobs`, `impact-misconception`, `impact-travel_immigration`, `improvement-accuracy`, `improvement-decision-making`, `improvement-future_readiness`, `improvement-health`, `improvement-personalisation`, `improvement-quality_of_life`, `improvement-speed`, `jobs-businessman`, `jobs-computer_operator`, `jobs-driver`, `jobs-nurse`, `jobs-surveillance`, `jobs-tutor`, `key_sectors-defence`, `key_sectors-disaster_management`, `key_sectors-education`, `key_sectors-elder_care`, `key_sectors-entertainment`, `key_sectors-finance`, `key_sectors-health`, `key_sectors-manufacturing`, `key_sectors-marketing`, `key_sectors-technology`, `key_sectors-transport`, `negative_impacts-control`, `negative_impacts-danger_to_humans`, `negative_impacts-dependency`, `negative_impacts-deskilling`, `negative_impacts-domination`, `negative_impacts-enslavement`, `negative_impacts-general`, `negative_impacts-immobility`, `negative_impacts-lack_of_inclusion`, `negative_impacts-lack_of_information`, `negative_impacts-laziness`, `positive_impacts-automation`, `positive_impacts-autonomy`, `positive_impacts-corruption_reduction`, `positive_impacts-cost_reduction`, `positive_impacts-drug_discovery`, `positive_impacts-general`, `positive_impacts-greater_enjoyment`, `positive_impacts-health`, `positive_impacts-invention`, `positive_impacts-productivity`, `positive_impacts-stress_reduction`, `positive_impacts-upskilling`, `progress-economy`, `progress-holistic`, `progress-now`, `requirements-basic_income`, `requirements-informed_engagement`, `requirements-oversight`, `requirements-regulation`, `safety-cybersecurity`, `safety-home`, `safety-privacy`, `safety-travel`, `safety-women`

### Inventions — machine leaves with no counterpart of his

`adoption-social_change`, `applications-automation`, `applications-data_driven_systems`, `applications-healthcare`, `applications-industry_and_transport`, `future-imagined_scenario`, `future-inevitability`, `future-superintelligence`, `future-uncertainty`, `governance-responsible_development`, `negative_impacts-dependence`, `negative_impacts-inequality`, `negative_impacts-unskilled_workers`
