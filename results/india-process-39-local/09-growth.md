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

Batch size 10; 91 distinct code(s) in all; **no batch admitted nothing new** — the curve has not flattened.

| batch | responses | cumulative responses | new codes | cumulative codes | new codes per response | spike |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 10 | 10 | 60 | 60 | 6.000 | - |
| 2 | 10 | 20 | 6 | 66 | 0.600 | - |
| 3 | 10 | 30 | 9 | 75 | 0.900 | - |
| 4 | 9 | 39 | 16 | 91 | 1.778 | - |

No batch met the spike rule.

## Saturation over the machine run

Batch size 10; 91 distinct codes; **not saturated**: every batch introduced new codes.

The curve is the growth table above (the two are one fact read two ways, and a
test asserts they agree batch by batch), so it is not repeated here.

Read this as a property of these coders on this sample, not as a finding that
the corpus has run out of ideas.
