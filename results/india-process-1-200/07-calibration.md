# 07 - Threshold calibration against his coding

Space `lexical-v1-512`; from 312 human and 371 machine codings over 39 responses.
The module reports; it never writes a threshold. `CodingRules` in `gaf/config.py` is unchanged.

| threshold | unit | units | positives | current | recommended | F1 at current | best F1 | F1 plateau |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `tau_fit` | machine code applications | 371 | 371 | 0.300 | 0.800 | 0.984 | 1.000 | 0.6-1.0 |
| `tau_high` | candidate/nearest-neighbour pairs | 20 | 1 | 0.800 | 0.950 | 0.500 | 0.667 | 0.9-1.0 |
| `tau_low` | candidate/nearest-neighbour pairs | 20 | 19 | 0.450 | 0.950 | 0.480 | 0.973 | 0.9-1.0 |

## The module's own notes

- tau_fit's F1 maximum is flat from 0.60 to 1.00, so this golden set barely discriminates it.
- tau_high rests on only 20 units, which is too few to move a threshold on; treat the curve as a shape, not a measurement.
- tau_low rests on only 20 units, which is too few to move a threshold on; treat the curve as a shape, not a measurement.

## Narrative

Threshold calibration ran in embedding space lexical-v1-512 against 371 machine codings and 312 human codings across 39 responses. tau_fit moves from 0.30 to 0.80: over 371 machine code applications (371 of them unsupported by the human coding), F1 of judge escalation peaks at 1.000 across grid values 0.60 to 1.00, against 0.984 at the provisional value. tau_high moves from 0.80 to 0.95: over 20 candidate/nearest-neighbour pairs (1 of them the same code in the human coding), F1 of auto-merge peaks at 0.667 across grid values 0.90 to 1.00, against 0.500 at the provisional value. tau_low moves from 0.45 to 0.95: over 20 candidate/nearest-neighbour pairs (19 of them absent from the human coding), F1 of auto-create peaks at 0.973 across grid values 0.90 to 1.00, against 0.480 at the provisional value. tau_fit's F1 maximum is flat from 0.60 to 1.00, so this golden set barely discriminates it. tau_high rests on only 20 units, which is too few to move a threshold on; treat the curve as a shape, not a measurement. tau_low rests on only 20 units, which is too few to move a threshold on; treat the curve as a shape, not a measurement. These are recommendations only. CodingRules is not modified by this function; a threshold changes only through a reported, versioned calibration artefact.

## Curve - `tau_fit` (judge escalation vs unsupported by the human coding)

| threshold | TP | FP | FN | TN | precision | recall | F1 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.000 | 0 | 0 | 371 | 0 | 0.000 | 0.000 | 0.000 |
| 0.050 | 321 | 0 | 50 | 0 | 1.000 | 0.865 | 0.928 |
| 0.100 | 321 | 0 | 50 | 0 | 1.000 | 0.865 | 0.928 |
| 0.150 | 329 | 0 | 42 | 0 | 1.000 | 0.887 | 0.940 |
| 0.200 | 345 | 0 | 26 | 0 | 1.000 | 0.930 | 0.964 |
| 0.250 | 355 | 0 | 16 | 0 | 1.000 | 0.957 | 0.978 |
| 0.300 | 359 | 0 | 12 | 0 | 1.000 | 0.968 | 0.984 |
| 0.350 | 364 | 0 | 7 | 0 | 1.000 | 0.981 | 0.990 |
| 0.400 | 369 | 0 | 2 | 0 | 1.000 | 0.995 | 0.997 |
| 0.450 | 370 | 0 | 1 | 0 | 1.000 | 0.997 | 0.999 |
| 0.500 | 370 | 0 | 1 | 0 | 1.000 | 0.997 | 0.999 |
| 0.550 | 370 | 0 | 1 | 0 | 1.000 | 0.997 | 0.999 |
| 0.600 | 371 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.650 | 371 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.700 | 371 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.750 | 371 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.800 | 371 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.850 | 371 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.900 | 371 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.950 | 371 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 1.000 | 371 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |

## Curve - `tau_high` (auto-merge vs the same code in the human coding)

| threshold | TP | FP | FN | TN | precision | recall | F1 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.000 | 1 | 19 | 0 | 0 | 0.050 | 1.000 | 0.095 |
| 0.050 | 1 | 19 | 0 | 0 | 0.050 | 1.000 | 0.095 |
| 0.100 | 1 | 19 | 0 | 0 | 0.050 | 1.000 | 0.095 |
| 0.150 | 1 | 19 | 0 | 0 | 0.050 | 1.000 | 0.095 |
| 0.200 | 1 | 19 | 0 | 0 | 0.050 | 1.000 | 0.095 |
| 0.250 | 1 | 19 | 0 | 0 | 0.050 | 1.000 | 0.095 |
| 0.300 | 1 | 19 | 0 | 0 | 0.050 | 1.000 | 0.095 |
| 0.350 | 1 | 19 | 0 | 0 | 0.050 | 1.000 | 0.095 |
| 0.400 | 1 | 18 | 0 | 1 | 0.053 | 1.000 | 0.100 |
| 0.450 | 1 | 13 | 0 | 6 | 0.071 | 1.000 | 0.133 |
| 0.500 | 1 | 13 | 0 | 6 | 0.071 | 1.000 | 0.133 |
| 0.550 | 1 | 7 | 0 | 12 | 0.125 | 1.000 | 0.222 |
| 0.600 | 1 | 6 | 0 | 13 | 0.143 | 1.000 | 0.250 |
| 0.650 | 1 | 6 | 0 | 13 | 0.143 | 1.000 | 0.250 |
| 0.700 | 1 | 3 | 0 | 16 | 0.250 | 1.000 | 0.400 |
| 0.750 | 1 | 3 | 0 | 16 | 0.250 | 1.000 | 0.400 |
| 0.800 | 1 | 2 | 0 | 17 | 0.333 | 1.000 | 0.500 |
| 0.850 | 1 | 2 | 0 | 17 | 0.333 | 1.000 | 0.500 |
| 0.900 | 1 | 1 | 0 | 18 | 0.500 | 1.000 | 0.667 |
| 0.950 | 1 | 1 | 0 | 18 | 0.500 | 1.000 | 0.667 |
| 1.000 | 1 | 1 | 0 | 18 | 0.500 | 1.000 | 0.667 |

## Curve - `tau_low` (auto-create vs absent from the human coding)

| threshold | TP | FP | FN | TN | precision | recall | F1 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.000 | 0 | 0 | 19 | 1 | 0.000 | 0.000 | 0.000 |
| 0.050 | 0 | 0 | 19 | 1 | 0.000 | 0.000 | 0.000 |
| 0.100 | 0 | 0 | 19 | 1 | 0.000 | 0.000 | 0.000 |
| 0.150 | 0 | 0 | 19 | 1 | 0.000 | 0.000 | 0.000 |
| 0.200 | 0 | 0 | 19 | 1 | 0.000 | 0.000 | 0.000 |
| 0.250 | 0 | 0 | 19 | 1 | 0.000 | 0.000 | 0.000 |
| 0.300 | 0 | 0 | 19 | 1 | 0.000 | 0.000 | 0.000 |
| 0.350 | 0 | 0 | 19 | 1 | 0.000 | 0.000 | 0.000 |
| 0.400 | 1 | 0 | 18 | 1 | 1.000 | 0.053 | 0.100 |
| 0.450 | 6 | 0 | 13 | 1 | 1.000 | 0.316 | 0.480 |
| 0.500 | 6 | 0 | 13 | 1 | 1.000 | 0.316 | 0.480 |
| 0.550 | 12 | 0 | 7 | 1 | 1.000 | 0.632 | 0.774 |
| 0.600 | 13 | 0 | 6 | 1 | 1.000 | 0.684 | 0.812 |
| 0.650 | 13 | 0 | 6 | 1 | 1.000 | 0.684 | 0.812 |
| 0.700 | 16 | 0 | 3 | 1 | 1.000 | 0.842 | 0.914 |
| 0.750 | 16 | 0 | 3 | 1 | 1.000 | 0.842 | 0.914 |
| 0.800 | 17 | 0 | 2 | 1 | 1.000 | 0.895 | 0.944 |
| 0.850 | 17 | 0 | 2 | 1 | 1.000 | 0.895 | 0.944 |
| 0.900 | 18 | 0 | 1 | 1 | 1.000 | 0.947 | 0.973 |
| 0.950 | 18 | 0 | 1 | 1 | 1.000 | 0.947 | 0.973 |
| 1.000 | 18 | 0 | 1 | 1 | 1.000 | 0.947 | 0.973 |
