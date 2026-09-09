# 07 - Threshold calibration against his coding

Space `lexical-v1-512`; from 147 human and 197 machine codings over 20 responses.
The module reports; it never writes a threshold. `CodingRules` in `gaf/config.py` is unchanged.

| threshold | unit | units | positives | current | recommended | F1 at current | best F1 | F1 plateau |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `tau_fit` | machine code applications | 197 | 197 | 0.300 | 0.750 | 0.987 | 1.000 | 0.45-1.0 |
| `tau_high` | candidate/nearest-neighbour pairs | 18 | 1 | 0.800 | 0.950 | 0.500 | 0.667 | 0.9-1.0 |
| `tau_low` | candidate/nearest-neighbour pairs | 18 | 17 | 0.450 | 0.950 | 0.455 | 0.970 | 0.9-1.0 |

## The module's own notes

- tau_fit's F1 maximum is flat from 0.45 to 1.00, so this golden set barely discriminates it.
- tau_high rests on only 18 units, which is too few to move a threshold on; treat the curve as a shape, not a measurement.
- tau_low rests on only 18 units, which is too few to move a threshold on; treat the curve as a shape, not a measurement.

## Narrative

Threshold calibration ran in embedding space lexical-v1-512 against 197 machine codings and 147 human codings across 20 responses. tau_fit moves from 0.30 to 0.75: over 197 machine code applications (197 of them unsupported by the human coding), F1 of judge escalation peaks at 1.000 across grid values 0.45 to 1.00, against 0.987 at the provisional value. tau_high moves from 0.80 to 0.95: over 18 candidate/nearest-neighbour pairs (1 of them the same code in the human coding), F1 of auto-merge peaks at 0.667 across grid values 0.90 to 1.00, against 0.500 at the provisional value. tau_low moves from 0.45 to 0.95: over 18 candidate/nearest-neighbour pairs (17 of them absent from the human coding), F1 of auto-create peaks at 0.970 across grid values 0.90 to 1.00, against 0.455 at the provisional value. tau_fit's F1 maximum is flat from 0.45 to 1.00, so this golden set barely discriminates it. tau_high rests on only 18 units, which is too few to move a threshold on; treat the curve as a shape, not a measurement. tau_low rests on only 18 units, which is too few to move a threshold on; treat the curve as a shape, not a measurement. These are recommendations only. CodingRules is not modified by this function; a threshold changes only through a reported, versioned calibration artefact.

## Curve - `tau_fit` (judge escalation vs unsupported by the human coding)

| threshold | TP | FP | FN | TN | precision | recall | F1 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.000 | 0 | 0 | 197 | 0 | 0.000 | 0.000 | 0.000 |
| 0.050 | 174 | 0 | 23 | 0 | 1.000 | 0.883 | 0.938 |
| 0.100 | 174 | 0 | 23 | 0 | 1.000 | 0.883 | 0.938 |
| 0.150 | 179 | 0 | 18 | 0 | 1.000 | 0.909 | 0.952 |
| 0.200 | 186 | 0 | 11 | 0 | 1.000 | 0.944 | 0.971 |
| 0.250 | 191 | 0 | 6 | 0 | 1.000 | 0.970 | 0.985 |
| 0.300 | 192 | 0 | 5 | 0 | 1.000 | 0.975 | 0.987 |
| 0.350 | 193 | 0 | 4 | 0 | 1.000 | 0.980 | 0.990 |
| 0.400 | 196 | 0 | 1 | 0 | 1.000 | 0.995 | 0.997 |
| 0.450 | 197 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.500 | 197 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.550 | 197 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.600 | 197 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.650 | 197 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.700 | 197 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.750 | 197 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.800 | 197 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.850 | 197 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.900 | 197 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 0.950 | 197 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 1.000 | 197 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |

## Curve - `tau_high` (auto-merge vs the same code in the human coding)

| threshold | TP | FP | FN | TN | precision | recall | F1 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.000 | 1 | 17 | 0 | 0 | 0.056 | 1.000 | 0.105 |
| 0.050 | 1 | 17 | 0 | 0 | 0.056 | 1.000 | 0.105 |
| 0.100 | 1 | 17 | 0 | 0 | 0.056 | 1.000 | 0.105 |
| 0.150 | 1 | 17 | 0 | 0 | 0.056 | 1.000 | 0.105 |
| 0.200 | 1 | 17 | 0 | 0 | 0.056 | 1.000 | 0.105 |
| 0.250 | 1 | 17 | 0 | 0 | 0.056 | 1.000 | 0.105 |
| 0.300 | 1 | 17 | 0 | 0 | 0.056 | 1.000 | 0.105 |
| 0.350 | 1 | 17 | 0 | 0 | 0.056 | 1.000 | 0.105 |
| 0.400 | 1 | 16 | 0 | 1 | 0.059 | 1.000 | 0.111 |
| 0.450 | 1 | 12 | 0 | 5 | 0.077 | 1.000 | 0.143 |
| 0.500 | 1 | 12 | 0 | 5 | 0.077 | 1.000 | 0.143 |
| 0.550 | 1 | 7 | 0 | 10 | 0.125 | 1.000 | 0.222 |
| 0.600 | 1 | 6 | 0 | 11 | 0.143 | 1.000 | 0.250 |
| 0.650 | 1 | 6 | 0 | 11 | 0.143 | 1.000 | 0.250 |
| 0.700 | 1 | 3 | 0 | 14 | 0.250 | 1.000 | 0.400 |
| 0.750 | 1 | 3 | 0 | 14 | 0.250 | 1.000 | 0.400 |
| 0.800 | 1 | 2 | 0 | 15 | 0.333 | 1.000 | 0.500 |
| 0.850 | 1 | 2 | 0 | 15 | 0.333 | 1.000 | 0.500 |
| 0.900 | 1 | 1 | 0 | 16 | 0.500 | 1.000 | 0.667 |
| 0.950 | 1 | 1 | 0 | 16 | 0.500 | 1.000 | 0.667 |
| 1.000 | 1 | 1 | 0 | 16 | 0.500 | 1.000 | 0.667 |

## Curve - `tau_low` (auto-create vs absent from the human coding)

| threshold | TP | FP | FN | TN | precision | recall | F1 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.000 | 0 | 0 | 17 | 1 | 0.000 | 0.000 | 0.000 |
| 0.050 | 0 | 0 | 17 | 1 | 0.000 | 0.000 | 0.000 |
| 0.100 | 0 | 0 | 17 | 1 | 0.000 | 0.000 | 0.000 |
| 0.150 | 0 | 0 | 17 | 1 | 0.000 | 0.000 | 0.000 |
| 0.200 | 0 | 0 | 17 | 1 | 0.000 | 0.000 | 0.000 |
| 0.250 | 0 | 0 | 17 | 1 | 0.000 | 0.000 | 0.000 |
| 0.300 | 0 | 0 | 17 | 1 | 0.000 | 0.000 | 0.000 |
| 0.350 | 0 | 0 | 17 | 1 | 0.000 | 0.000 | 0.000 |
| 0.400 | 1 | 0 | 16 | 1 | 1.000 | 0.059 | 0.111 |
| 0.450 | 5 | 0 | 12 | 1 | 1.000 | 0.294 | 0.455 |
| 0.500 | 5 | 0 | 12 | 1 | 1.000 | 0.294 | 0.455 |
| 0.550 | 10 | 0 | 7 | 1 | 1.000 | 0.588 | 0.741 |
| 0.600 | 11 | 0 | 6 | 1 | 1.000 | 0.647 | 0.786 |
| 0.650 | 11 | 0 | 6 | 1 | 1.000 | 0.647 | 0.786 |
| 0.700 | 14 | 0 | 3 | 1 | 1.000 | 0.824 | 0.903 |
| 0.750 | 14 | 0 | 3 | 1 | 1.000 | 0.824 | 0.903 |
| 0.800 | 15 | 0 | 2 | 1 | 1.000 | 0.882 | 0.938 |
| 0.850 | 15 | 0 | 2 | 1 | 1.000 | 0.882 | 0.938 |
| 0.900 | 16 | 0 | 1 | 1 | 1.000 | 0.941 | 0.970 |
| 0.950 | 16 | 0 | 1 | 1 | 1.000 | 0.941 | 0.970 |
| 1.000 | 16 | 0 | 1 | 1 | 1.000 | 0.941 | 0.970 |
