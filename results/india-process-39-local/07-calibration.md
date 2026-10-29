# 07 - Threshold calibration against his coding

Space `local-embeddinggemma-768`; from 157 human and 144 machine codings over 20 responses.
The module reports; it never writes a threshold. `CodingRules` in `gaf/config.py` is unchanged.

| threshold | unit | units | positives | current | recommended | F1 at current | best F1 | F1 plateau |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `tau_fit` | machine code applications | 144 | 137 | 0.300 | 0.950 | 0.084 | 0.975 | 0.85-1.0 |
| `tau_high` | candidate/nearest-neighbour pairs | 68 | 4 | 0.800 | 0.950 | 0.500 | 1.000 | 0.9-1.0 |
| `tau_low` | candidate/nearest-neighbour pairs | 68 | 64 | 0.450 | 0.950 | 0.000 | 1.000 | 0.9-1.0 |

## The module's own notes


## Narrative

Threshold calibration ran in embedding space local-embeddinggemma-768 against 144 machine codings and 157 human codings across 20 responses. tau_fit moves from 0.30 to 0.95: over 144 machine code applications (137 of them unsupported by the human coding), F1 of judge escalation peaks at 0.975 across grid values 0.85 to 1.00, against 0.084 at the provisional value. tau_high moves from 0.80 to 0.95: over 68 candidate/nearest-neighbour pairs (4 of them the same code in the human coding), F1 of auto-merge peaks at 1.000 across grid values 0.90 to 1.00, against 0.500 at the provisional value. tau_low moves from 0.45 to 0.95: over 68 candidate/nearest-neighbour pairs (64 of them absent from the human coding), F1 of auto-create peaks at 1.000 across grid values 0.90 to 1.00, against 0.000 at the provisional value. These are recommendations only. CodingRules is not modified by this function; a threshold changes only through a reported, versioned calibration artefact.

## Curve - `tau_fit` (judge escalation vs unsupported by the human coding)

| threshold | TP | FP | FN | TN | precision | recall | F1 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.000 | 0 | 0 | 137 | 7 | 0.000 | 0.000 | 0.000 |
| 0.050 | 0 | 0 | 137 | 7 | 0.000 | 0.000 | 0.000 |
| 0.100 | 0 | 0 | 137 | 7 | 0.000 | 0.000 | 0.000 |
| 0.150 | 0 | 0 | 137 | 7 | 0.000 | 0.000 | 0.000 |
| 0.200 | 1 | 0 | 136 | 7 | 1.000 | 0.007 | 0.014 |
| 0.250 | 3 | 0 | 134 | 7 | 1.000 | 0.022 | 0.043 |
| 0.300 | 6 | 0 | 131 | 7 | 1.000 | 0.044 | 0.084 |
| 0.350 | 21 | 0 | 116 | 7 | 1.000 | 0.153 | 0.266 |
| 0.400 | 33 | 1 | 104 | 6 | 0.971 | 0.241 | 0.386 |
| 0.450 | 56 | 1 | 81 | 6 | 0.982 | 0.409 | 0.577 |
| 0.500 | 82 | 2 | 55 | 5 | 0.976 | 0.599 | 0.742 |
| 0.550 | 97 | 4 | 40 | 3 | 0.960 | 0.708 | 0.815 |
| 0.600 | 117 | 6 | 20 | 1 | 0.951 | 0.854 | 0.900 |
| 0.650 | 125 | 7 | 12 | 0 | 0.947 | 0.912 | 0.929 |
| 0.700 | 132 | 7 | 5 | 0 | 0.950 | 0.964 | 0.957 |
| 0.750 | 135 | 7 | 2 | 0 | 0.951 | 0.985 | 0.968 |
| 0.800 | 136 | 7 | 1 | 0 | 0.951 | 0.993 | 0.971 |
| 0.850 | 137 | 7 | 0 | 0 | 0.951 | 1.000 | 0.975 |
| 0.900 | 137 | 7 | 0 | 0 | 0.951 | 1.000 | 0.975 |
| 0.950 | 137 | 7 | 0 | 0 | 0.951 | 1.000 | 0.975 |
| 1.000 | 137 | 7 | 0 | 0 | 0.951 | 1.000 | 0.975 |

## Curve - `tau_high` (auto-merge vs the same code in the human coding)

| threshold | TP | FP | FN | TN | precision | recall | F1 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.000 | 4 | 64 | 0 | 0 | 0.059 | 1.000 | 0.111 |
| 0.050 | 4 | 64 | 0 | 0 | 0.059 | 1.000 | 0.111 |
| 0.100 | 4 | 64 | 0 | 0 | 0.059 | 1.000 | 0.111 |
| 0.150 | 4 | 64 | 0 | 0 | 0.059 | 1.000 | 0.111 |
| 0.200 | 4 | 64 | 0 | 0 | 0.059 | 1.000 | 0.111 |
| 0.250 | 4 | 64 | 0 | 0 | 0.059 | 1.000 | 0.111 |
| 0.300 | 4 | 64 | 0 | 0 | 0.059 | 1.000 | 0.111 |
| 0.350 | 4 | 64 | 0 | 0 | 0.059 | 1.000 | 0.111 |
| 0.400 | 4 | 64 | 0 | 0 | 0.059 | 1.000 | 0.111 |
| 0.450 | 4 | 64 | 0 | 0 | 0.059 | 1.000 | 0.111 |
| 0.500 | 4 | 63 | 0 | 1 | 0.060 | 1.000 | 0.113 |
| 0.550 | 4 | 61 | 0 | 3 | 0.062 | 1.000 | 0.116 |
| 0.600 | 4 | 56 | 0 | 8 | 0.067 | 1.000 | 0.125 |
| 0.650 | 4 | 44 | 0 | 20 | 0.083 | 1.000 | 0.154 |
| 0.700 | 4 | 26 | 0 | 38 | 0.133 | 1.000 | 0.235 |
| 0.750 | 4 | 11 | 0 | 53 | 0.267 | 1.000 | 0.421 |
| 0.800 | 4 | 8 | 0 | 56 | 0.333 | 1.000 | 0.500 |
| 0.850 | 4 | 2 | 0 | 62 | 0.667 | 1.000 | 0.800 |
| 0.900 | 4 | 0 | 0 | 64 | 1.000 | 1.000 | 1.000 |
| 0.950 | 4 | 0 | 0 | 64 | 1.000 | 1.000 | 1.000 |
| 1.000 | 4 | 0 | 0 | 64 | 1.000 | 1.000 | 1.000 |

## Curve - `tau_low` (auto-create vs absent from the human coding)

| threshold | TP | FP | FN | TN | precision | recall | F1 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.000 | 0 | 0 | 64 | 4 | 0.000 | 0.000 | 0.000 |
| 0.050 | 0 | 0 | 64 | 4 | 0.000 | 0.000 | 0.000 |
| 0.100 | 0 | 0 | 64 | 4 | 0.000 | 0.000 | 0.000 |
| 0.150 | 0 | 0 | 64 | 4 | 0.000 | 0.000 | 0.000 |
| 0.200 | 0 | 0 | 64 | 4 | 0.000 | 0.000 | 0.000 |
| 0.250 | 0 | 0 | 64 | 4 | 0.000 | 0.000 | 0.000 |
| 0.300 | 0 | 0 | 64 | 4 | 0.000 | 0.000 | 0.000 |
| 0.350 | 0 | 0 | 64 | 4 | 0.000 | 0.000 | 0.000 |
| 0.400 | 0 | 0 | 64 | 4 | 0.000 | 0.000 | 0.000 |
| 0.450 | 0 | 0 | 64 | 4 | 0.000 | 0.000 | 0.000 |
| 0.500 | 1 | 0 | 63 | 4 | 1.000 | 0.016 | 0.031 |
| 0.550 | 3 | 0 | 61 | 4 | 1.000 | 0.047 | 0.090 |
| 0.600 | 8 | 0 | 56 | 4 | 1.000 | 0.125 | 0.222 |
| 0.650 | 20 | 0 | 44 | 4 | 1.000 | 0.312 | 0.476 |
| 0.700 | 38 | 0 | 26 | 4 | 1.000 | 0.594 | 0.745 |
| 0.750 | 53 | 0 | 11 | 4 | 1.000 | 0.828 | 0.906 |
| 0.800 | 56 | 0 | 8 | 4 | 1.000 | 0.875 | 0.933 |
| 0.850 | 62 | 0 | 2 | 4 | 1.000 | 0.969 | 0.984 |
| 0.900 | 64 | 0 | 0 | 4 | 1.000 | 1.000 | 1.000 |
| 0.950 | 64 | 0 | 0 | 4 | 1.000 | 1.000 | 1.000 |
| 1.000 | 64 | 0 | 0 | 4 | 1.000 | 1.000 | 1.000 |
