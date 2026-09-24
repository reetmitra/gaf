# 09 - Code growth, the spike rule and saturation

Growth counts **admissions**: the batch in which each code entered the codebook
for the first time. A batch spikes when it admits at least
4 new codes *and* at least 2x the median of the
previous 3 batches; before a baseline exists the absolute ceiling of
8 per batch applies instead. Both rules are uncalibrated (ADR-0033)
and both are reported rather than acted on here.

**Batches here are batches of *coded* responses.** The curve is cut every
10 responses that carry at least one code, in the order they were coded;
a response nobody coded does not advance it. For a run that codes everything the
two readings coincide, and for a coding that covers part of a corpus they do not.

## Code growth over his coding

Batch size 10; 109 distinct code(s) in all; **no batch admitted nothing new** — the curve has not flattened.

| batch | responses | cumulative responses | new codes | cumulative codes | new codes per response | spike |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 10 | 10 | 47 | 47 | 4.700 | - |
| 2 | 10 | 20 | 29 | 76 | 2.900 | - |
| 3 | 10 | 30 | 23 | 99 | 2.300 | - |
| 4 | 9 | 39 | 10 | 109 | 1.111 | - |

No batch met the spike rule.

> The run records a growth curve of its own, built from its admissions at its
> own batch size. It is the one the handover trace and the timeline are keyed to. It agrees with the analysis tail's point for point, so the table below reads the same either way.

## Code growth over the machine run

Batch size 10; 22 distinct code(s) in all; first batch that admitted nothing new: batch 4.

| batch | responses | cumulative responses | new codes | cumulative codes | new codes per response | spike |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 10 | 10 | 15 | 15 | 1.500 | - |
| 2 | 10 | 20 | 3 | 18 | 0.300 | - |
| 3 | 10 | 30 | 2 | 20 | 0.200 | - |
| 4 | 10 | 40 | 0 | 20 | 0.000 | - |
| 5 | 10 | 50 | 0 | 20 | 0.000 | - |
| 6 | 10 | 60 | 0 | 20 | 0.000 | - |
| 7 | 10 | 70 | 0 | 20 | 0.000 | - |
| 8 | 10 | 80 | 0 | 20 | 0.000 | - |
| 9 | 10 | 90 | 0 | 20 | 0.000 | - |
| 10 | 10 | 100 | 0 | 20 | 0.000 | - |
| 11 | 10 | 110 | 0 | 20 | 0.000 | - |
| 12 | 10 | 120 | 0 | 20 | 0.000 | - |
| 13 | 10 | 130 | 1 | 21 | 0.100 | - |
| 14 | 10 | 140 | 0 | 21 | 0.000 | - |
| 15 | 10 | 150 | 1 | 22 | 0.100 | - |
| 16 | 10 | 160 | 0 | 22 | 0.000 | - |
| 17 | 10 | 170 | 0 | 22 | 0.000 | - |
| 18 | 10 | 180 | 0 | 22 | 0.000 | - |
| 19 | 10 | 190 | 0 | 22 | 0.000 | - |
| 20 | 10 | 200 | 0 | 22 | 0.000 | - |

No batch met the spike rule.

## Saturation over the machine run

Batch size 10; 22 distinct codes; **saturated at batch 4** — that batch admitted nothing new.

The curve is the growth table above (the two are one fact read two ways, and a
test asserts they agree batch by batch), so it is not repeated here.

A stand-in coder built on a keyword table saturates because its vocabulary is
finite, not because the corpus ran out of ideas. Read this as a property of the
offline coder, not a finding about the corpus.
