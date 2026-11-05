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

> The run records a growth curve of its own, built from its admissions at its
> own batch size. It is the one the handover trace and the timeline are keyed to. It agrees with the analysis tail's point for point, so the table below reads the same either way.

## Code growth over the machine run

Batch size 10; 162 distinct code(s) in all; first batch that admitted nothing new: batch 18.

| batch | responses | cumulative responses | new codes | cumulative codes | new codes per response | spike |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 10 | 10 | 60 | 60 | 6.000 | - |
| 2 | 10 | 20 | 6 | 66 | 0.600 | - |
| 3 | 10 | 30 | 9 | 75 | 0.900 | - |
| 4 | 10 | 40 | 14 | 89 | 1.400 | - |
| 5 | 10 | 50 | 7 | 96 | 0.700 | - |
| 6 | 10 | 60 | 8 | 104 | 0.800 | - |
| 7 | 10 | 70 | 7 | 111 | 0.700 | - |
| 8 | 10 | 80 | 6 | 117 | 0.600 | - |
| 9 | 10 | 90 | 4 | 121 | 0.400 | - |
| 10 | 10 | 100 | 4 | 125 | 0.400 | - |
| 11 | 10 | 110 | 6 | 131 | 0.600 | - |
| 12 | 10 | 120 | 3 | 134 | 0.300 | - |
| 13 | 10 | 130 | 5 | 139 | 0.500 | - |
| 14 | 10 | 140 | 3 | 142 | 0.300 | - |
| 15 | 10 | 150 | 6 | 148 | 0.600 | yes (ratio) |
| 16 | 10 | 160 | 6 | 154 | 0.600 | - |
| 17 | 10 | 170 | 4 | 158 | 0.400 | - |
| 18 | 10 | 180 | 0 | 158 | 0.000 | - |
| 19 | 10 | 190 | 2 | 160 | 0.200 | - |
| 20 | 10 | 200 | 2 | 162 | 0.200 | - |

**Spikes: 1.**

- batch 15: 6 new code(s), rule `ratio`, baseline 3.00, window 3, ratio 2.00

## Saturation over the machine run

Batch size 10; 162 distinct codes; **saturated at batch 18** — that batch admitted nothing new.

The curve is the growth table above (the two are one fact read two ways, and a
test asserts they agree batch by batch), so it is not repeated here.

Read this as a property of these coders on this sample, not as a finding that
the corpus has run out of ideas.
