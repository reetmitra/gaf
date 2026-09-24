# 11 - Pattern mapping: which responses look alike

A pattern group is a set of responses that touch exactly the same families. It is a
description of the coding, not a claim about the respondents: two responses in one
group may say opposite things about the same subjects.

## Patterns in his coding

39 responses x 109 codes; minimum support 2.
2 pattern group(s) — responses touching exactly the same set of
families — and 35 response(s) whose family signature is unique.

| size | families touched | responses |
|---:|---|---|
| 2 | `AI`, `future`, `negative_impacts` | 67, 100 |
| 2 | `future`, `improvement`, `key_sectors`, `positive_impacts` | 88, 94 |

### Family co-occurrence (responses carrying both)

| family | AI | adoption | applications | ease | efficiency | future | impact | improvement | jobs | key_sectors | negative_impacts | positive_impacts | progress | requirements | safety |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `AI` | 5 | 1 | 1 | 1 | 1 | 4 | 0 | 2 | 0 | 2 | 3 | 2 | 1 | 0 | 0 |
| `adoption` | 1 | 9 | 5 | 4 | 0 | 8 | 2 | 2 | 1 | 1 | 3 | 7 | 1 | 0 | 0 |
| `applications` | 1 | 5 | 21 | 13 | 6 | 12 | 5 | 8 | 4 | 4 | 6 | 13 | 3 | 2 | 3 |
| `ease` | 1 | 4 | 13 | 18 | 6 | 8 | 4 | 5 | 3 | 3 | 6 | 10 | 4 | 2 | 3 |
| `efficiency` | 1 | 0 | 6 | 6 | 10 | 4 | 3 | 6 | 1 | 2 | 5 | 9 | 1 | 3 | 1 |
| `future` | 4 | 8 | 12 | 8 | 4 | 23 | 6 | 9 | 3 | 8 | 10 | 16 | 1 | 3 | 2 |
| `impact` | 0 | 2 | 5 | 4 | 3 | 6 | 9 | 4 | 1 | 2 | 5 | 7 | 0 | 3 | 1 |
| `improvement` | 2 | 2 | 8 | 5 | 6 | 9 | 4 | 14 | 3 | 6 | 5 | 13 | 1 | 2 | 1 |
| `jobs` | 0 | 1 | 4 | 3 | 1 | 3 | 1 | 3 | 5 | 2 | 1 | 3 | 1 | 1 | 2 |
| `key_sectors` | 2 | 1 | 4 | 3 | 2 | 8 | 2 | 6 | 2 | 11 | 4 | 8 | 1 | 1 | 2 |
| `negative_impacts` | 3 | 3 | 6 | 6 | 5 | 10 | 5 | 5 | 1 | 4 | 17 | 11 | 1 | 5 | 0 |
| `positive_impacts` | 2 | 7 | 13 | 10 | 9 | 16 | 7 | 13 | 3 | 8 | 11 | 24 | 2 | 4 | 2 |
| `progress` | 1 | 1 | 3 | 4 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 2 | 4 | 0 | 0 |
| `requirements` | 0 | 0 | 2 | 2 | 3 | 3 | 3 | 2 | 1 | 1 | 5 | 4 | 0 | 6 | 1 |
| `safety` | 0 | 0 | 3 | 3 | 1 | 2 | 1 | 1 | 2 | 2 | 0 | 2 | 0 | 1 | 4 |

### Code pairs that travel together (106 at or above support 2)

`lift` is the joint share over the product of the two individual shares: 1.0 is
chance, above 1.0 is more often than chance.

| code | code | support | share | lift |
|---|---|---:|---:|---:|
| `ease-work` | `efficiency` | 5 | 0.128 | 1.950 |
| `impact-jobs` | `negative_impacts-job_destruction` | 4 | 0.103 | 5.571 |
| `negative_impacts-general` | `positive_impacts-general` | 4 | 0.103 | 4.875 |
| `efficiency` | `improvement-accuracy` | 4 | 0.103 | 2.600 |
| `future-transformation` | `positive_impacts-problem-solving` | 4 | 0.103 | 2.438 |
| `ease-life` | `future-transformation` | 4 | 0.103 | 2.167 |
| `efficiency` | `positive_impacts-general` | 4 | 0.103 | 1.950 |
| `ease-life` | `ease-work` | 4 | 0.103 | 1.733 |
| `adoption-present` | `future-inevitability` | 3 | 0.077 | 5.571 |
| `future-positive` | `improvement-quality_of_life` | 3 | 0.077 | 4.875 |
| `applications-personal_assistant` | `ease-life` | 3 | 0.077 | 4.333 |
| `ease-life` | `positive_impacts-automation` | 3 | 0.077 | 4.333 |
| `ease-work` | `progress-holistic` | 3 | 0.077 | 3.900 |
| `improvement-accuracy` | `negative_impacts-job_destruction` | 3 | 0.077 | 2.786 |
| `adoption-high` | `future-transformation` | 3 | 0.077 | 2.438 |
| `improvement-accuracy` | `positive_impacts-general` | 3 | 0.077 | 2.438 |
| `future-inevitability` | `negative_impacts-job_destruction` | 3 | 0.077 | 2.388 |
| `adoption-high` | `ease-life` | 3 | 0.077 | 2.167 |
| `future-inevitability` | `future-transformation` | 3 | 0.077 | 2.089 |
| `future-transformation` | `negative_impacts-job_destruction` | 3 | 0.077 | 2.089 |

Triples at or above the same support: 47.

## Patterns in the machine run

200 responses x 22 codes; minimum support 2.
20 pattern group(s) — responses touching exactly the same set of
families — and 10 response(s) whose family signature is unique.

| size | families touched | responses |
|---:|---|---|
| 37 | `adoption`, `applications`, `future`, `positive_impacts` | 14, 15, 33, 42, 45, 51, 53, 84, 94, 155, 156, 185, 191, 203, 230, 235, 237, 317, 321, 324, 369, 372, 400, 401, 409, 434, 468, 502, 535, 545, 548, 554, 565, 572, 587, 589, 596 |
| 29 | `adoption`, `future`, `positive_impacts` | 22, 67, 90, 149, 162, 188, 219, 223, 234, 240, 244, 249, 252, 262, 278, 304, 346, 408, 415, 422, 436, 444, 452, 455, 517, 538, 555, 556, 575 |
| 28 | `adoption`, `applications`, `future` | 47, 52, 61, 82, 85, 167, 175, 245, 256, 258, 261, 314, 332, 375, 395, 424, 469, 472, 473, 474, 475, 477, 478, 513, 532, 551, 558, 578 |
| 19 | `adoption`, `applications`, `future`, `negative_impacts`, `positive_impacts` | 19, 48, 77, 81, 139, 170, 184, 208, 254, 272, 300, 353, 366, 376, 426, 451, 458, 576, 588 |
| 13 | `adoption`, `future` | 23, 43, 46, 95, 144, 341, 437, 499, 503, 509, 560, 574, 586 |
| 12 | `adoption`, `applications`, `future`, `negative_impacts` | 40, 87, 96, 154, 187, 192, 255, 337, 344, 405, 440, 536 |
| 11 | `adoption`, `future`, `negative_impacts`, `positive_impacts` | 11, 176, 196, 204, 315, 327, 335, 383, 398, 445, 559 |
| 9 | `adoption`, `future`, `negative_impacts` | 24, 44, 64, 100, 161, 166, 236, 454, 522 |
| 4 | `adoption`, `applications`, `future`, `governance`, `positive_impacts` | 73, 194, 391, 396 |
| 4 | `adoption`, `applications`, `positive_impacts` | 138, 418, 427, 448 |
| 4 | `applications`, `negative_impacts` | 133, 215, 247, 339 |
| 3 | `adoption`, `applications` | 357, 393, 476 |
| 3 | `applications`, `future` | 158, 217, 250 |
| 2 | `adoption`, `applications`, `future`, `governance`, `negative_impacts` | 248, 399 |
| 2 | `adoption`, `applications`, `future`, `governance`, `negative_impacts`, `positive_impacts` | 385, 571 |
| 2 | `adoption`, `applications`, `negative_impacts`, `positive_impacts` | 171, 491 |
| 2 | `adoption`, `future`, `governance`, `negative_impacts` | 79, 186 |
| 2 | `applications`, `future`, `negative_impacts`, `positive_impacts` | 80, 523 |
| 2 | `applications`, `positive_impacts` | 296, 429 |
| 2 | `future`, `positive_impacts` | 384, 542 |

### Family co-occurrence (responses carrying both)

| family | adoption | applications | future | governance | negative_impacts | positive_impacts |
|---|---:|---:|---:|---:|---:|---:|
| `adoption` | 183 | 114 | 171 | 13 | 62 | 112 |
| `applications` | 114 | 129 | 111 | 8 | 46 | 74 |
| `future` | 171 | 111 | 180 | 13 | 61 | 109 |
| `governance` | 13 | 8 | 13 | 13 | 7 | 8 |
| `negative_impacts` | 62 | 46 | 61 | 7 | 70 | 39 |
| `positive_impacts` | 112 | 74 | 109 | 8 | 39 | 120 |

### Code pairs that travel together (133 at or above support 2)

`lift` is the joint share over the product of the two individual shares: 1.0 is
chance, above 1.0 is more often than chance.

| code | code | support | share | lift |
|---|---|---:|---:|---:|
| `adoption-social_change` | `future-imagined_scenario` | 168 | 0.840 | 1.055 |
| `adoption-social_change` | `positive_impacts-problem_solving` | 78 | 0.390 | 1.050 |
| `future-imagined_scenario` | `positive_impacts-problem_solving` | 73 | 0.365 | 0.988 |
| `applications-automation` | `future-imagined_scenario` | 40 | 0.200 | 1.021 |
| `adoption-social_change` | `applications-automation` | 39 | 0.195 | 0.990 |
| `applications-healthcare` | `future-imagined_scenario` | 38 | 0.190 | 0.890 |
| `adoption-social_change` | `applications-education` | 37 | 0.185 | 1.060 |
| `adoption-social_change` | `applications-healthcare` | 35 | 0.175 | 0.815 |
| `applications-education` | `future-imagined_scenario` | 34 | 0.170 | 0.980 |
| `future-imagined_scenario` | `negative_impacts-dependence` | 33 | 0.165 | 1.059 |
| `adoption-social_change` | `negative_impacts-dependence` | 32 | 0.160 | 1.022 |
| `applications-industry_and_transport` | `future-imagined_scenario` | 31 | 0.155 | 0.995 |
| `future-imagined_scenario` | `positive_impacts-quality_of_life` | 31 | 0.155 | 0.995 |
| `adoption-social_change` | `applications-industry_and_transport` | 31 | 0.155 | 0.990 |
| `adoption-social_change` | `positive_impacts-quality_of_life` | 31 | 0.155 | 0.990 |
| `adoption-social_change` | `applications-data_driven_systems` | 25 | 0.125 | 0.931 |
| `future-imagined_scenario` | `negative_impacts-job_loss` | 22 | 0.110 | 0.916 |
| `applications-data_driven_systems` | `future-imagined_scenario` | 22 | 0.110 | 0.824 |
| `adoption-social_change` | `negative_impacts-job_loss` | 21 | 0.105 | 0.869 |
| `adoption-everyday_life` | `future-imagined_scenario` | 20 | 0.100 | 1.021 |

Triples at or above the same support: 262.
