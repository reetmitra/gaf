# 16 - Halting at the handover, and resuming without loss

`gaf run --halt-on-checkpoint` stops after the first batch whose verdict is
`checkpoint_due` — the point at which the decision matrix says a human should look
at the codebook. The run still closes normally: a short run is better than a
half-written one.

| what | value |
|---|---|
| halted at batch | 1 |
| responses coded | 10 |
| responses left uncoded | 190 |
| codes in the codebook at the stop | 15 |
| assignment rows | 104 |
| trigger | `health` |
| rule(s) fired | `handover.new_codes` |

> new codes this batch 15 > 8; the spike rule has no baseline yet: a ratio needs 3 coded batches behind it, so batch 1 is judged by the absolute ceiling alone

## Resuming

| what | value |
|---|---|
| rows written before the halt | 104 |
| rows written after resuming | 1848 |
| rows in an uninterrupted cold run | 1952 |
| rows the two halves share | 0 |
| rows where halted+resumed differs from cold | 0 |
| concatenation is row-for-row identical to the cold run | yes |
| codes at the end of the resumption | 22 |
| codes at the end of the cold run | 22 |

**Stopping at the handover and resuming costs nothing.** That is what makes the
human gate affordable: a researcher can be asked to look at the codebook after any
batch without the coding having to start again.
