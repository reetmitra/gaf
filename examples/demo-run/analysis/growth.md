> Cut the way run `demo` cut it: 14 response(s) in the order the run processed them, at its own batch size of 10. This is the curve the run's decision trace, handover verdicts and timeline are keyed to.

## Code growth

Source `assignments`; batch size 10; 14 distinct code(s) in total. First batch that admitted nothing new: not reached.

Batch numbers are 1-based, as everywhere else in this build.

| batch | responses | cumulative responses | new codes | cumulative codes | new codes per response | spike |
|---:|---:|---:|---:|---:|---:|:--|
| 1 | 10 | 10 | 12 | 12 | 1.200 | - |
| 2 | 4 | 14 | 2 | 14 | 0.500 | - |

### Spikes

_No batch met the spike rule._
