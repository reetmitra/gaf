# 03 - His coding against his own rules (structural checks S1-S6)

The rules are the ones transcribed from his working document into `docs/CODING_RULES.md`.
A WARN is kept and flagged and is never fatal; only an ERROR fails the gate.

| check | ERROR | WARN | INFO | what it checks |
|---|---:|---:|---:|---|
| S1 | 0 | 134 | 0 | name, description, evidence present |
| S2 | 0 | 0 | 0 | every quote locates in its response |
| S3 | 0 | 7 | 0 | two-level name grammar; sub-code before new top-level |
| S4 | 0 | 0 | 0 | at most two codes on one piece of text |
| S5 | 0 | 1 | 0 | the usual two to twelve codes per response |

**RESULT: PASS - no ERROR finding.**

## Findings other than S1

| check | severity | marker | subject | message | n |
|---|---|---|---|---|---:|
| S3 | WARN | sub_code_first | efficiency | The family 'efficiency' already exists in the codebook; consider a sub-code of it before adding another top-level code. | 7 |
| S5 | WARN | too_many_codes | 33 | Coder 'spreadsheet' produced 14 codes for this response, more than the usual 2 to 12. | 1 |

## S1 - missing description, 134 findings

The export carries code names and no definitions, so every response-code pair lacks one.
Not a coding fault; the codes concerned (76):

`AI-machine_communication`, `AI-tool`, `adoption-high`, `adoption-necessity`, `adoption-present`, `applications-chatbots`, `applications-decision-making`, `applications-friend`, `applications-information`, `applications-medical_care`, `applications-meetings`, `applications-navigation`, `applications-personal_assistant`, `applications-planning`, `applications-relationships`, `applications-robotics`, `applications-search`, `applications-self-driving_cars`, `applications-text_generation`, `applications-translation`, `ease-life`, `ease-travel`, `ease-work`, `efficiency`, `future-inevitability`, `future-positive`, `future-transformation`, `impact-global`, `impact-jobs`, `impact-travel_immigration`, `improvement-accuracy`, `improvement-personalisation`, `improvement-quality_of_life`, `improvement-speed`, `jobs-businessman`, `jobs-computer_operator`, `jobs-driver`, `jobs-nurse`, `jobs-surveillance`, `jobs-tutor`, `key-sectors-elder_care`, `key_sectors-defence`, `key_sectors-disaster_management`, `key_sectors-education`, `key_sectors-entertainment`, `key_sectors-health`, `key_sectors-marketing`, `key_sectors-technology`, `key_sectors-transport`, `negative_impacts-dependency`, `negative_impacts-deskilling`, `negative_impacts-enslavement`, `negative_impacts-general`, `negative_impacts-job_destruction`, `negative_impacts-laziness`, `negative_impacts-misuse`, `positive_impacts-automation`, `positive_impacts-autonomy`, `positive_impacts-corruption_reduction`, `positive_impacts-cost_reduction`, `positive_impacts-general`, `positive_impacts-greater_enjoyment`, `positive_impacts-jobs`, `positive_impacts-problem-solving`, `positive_impacts-productivity`, `positive_impacts-stress_reduction`, `progress-economy`, `progress-holistic`, `progress-now`, `requirements-basic_income`, `requirements-oversight`, `requirements-regulation`, `safety-cybersecurity`, `safety-home`, `safety-travel`, `safety-women`
