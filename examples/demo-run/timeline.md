## Timeline of code generation and change

Run `demo` — 14 response(s) coded over 2 batch(es).

### Batches

| batch | responses | new codes | merges | cumulative codes | judge calls |
|---:|---:|---:|---:|---:|---:|
| 1 | 10 | 12 | 18 | 12 | 0 |
| 2 | 4 | 2 | 11 | 14 | 0 |

Handover evaluated at every batch boundary:

- batch 1 handover: **checkpoint_due** — new codes this batch 12 > 8; the spike rule has no baseline yet: a ratio needs 3 coded batches behind it, so batch 1 is judged by the absolute ceiling alone
- batch 2 handover: **continue** — the spike rule has no baseline yet: a ratio needs 3 coded batches behind it, so batch 2 is judged by the absolute ceiling alone

### Snapshot diffs

Codes are matched by code id, then this run's own recorded rename operations; a rename is reported only where an operation recorded it, and never inferred. A code that only moved has no line at all, because re-parenting keeps a code's id and so changes nothing this diff can see.

- `snap-8c8e1bb384bd3da4` -> `snap-4041159865476169` (batch): 12 added, 0 removed, 0 renamed
  - added: 'adoption-social_change'
  - added: 'applications-automation'
  - added: 'applications-data_driven_systems'
  - added: 'applications-education'
  - added: 'applications-healthcare'
  - added: 'applications-industry_and_transport'
  - added: 'applications-personalisation'
  - added: 'future-imagined_scenario'
  - added: 'negative_impacts-dependence'
  - added: 'negative_impacts-job_loss'
  - added: 'positive_impacts-access'
  - added: 'positive_impacts-problem_solving'
- `snap-4041159865476169` -> `snap-3281fbd1f36b27ec` (batch): 2 added, 0 removed, 0 renamed
  - added: 'future-uncertainty'
  - added: 'positive_impacts-quality_of_life'

### Code biographies

| code | family | born | fate |
|---|---|---|---|
| adoption-social_change | adoption | response 203 (batch 1), proposed by coder_b | alive |
| applications-automation | applications | response 239 (batch 1), proposed by coder_a, coder_b | alive |
| applications-data_driven_systems | applications | response 203 (batch 1), proposed by coder_a, coder_b | alive |
| applications-education | applications | response 207 (batch 1), proposed by coder_a, coder_b | alive |
| applications-healthcare | applications | response 203 (batch 1), proposed by coder_a, coder_b | alive |
| applications-industry_and_transport | applications | response 212 (batch 1), proposed by coder_a, coder_b | alive |
| applications-personalisation | applications | response 212 (batch 1), proposed by coder_a, coder_b | alive |
| future-imagined_scenario | future | response 203 (batch 1), proposed by coder_a, coder_b | alive |
| future-uncertainty | future | response 258 (batch 2), proposed by coder_a, coder_b | alive |
| negative_impacts-dependence | negative_impacts | response 218 (batch 1), proposed by coder_a, coder_b | alive |
| negative_impacts-job_loss | negative_impacts | response 207 (batch 1), proposed by coder_a, coder_b | alive |
| positive_impacts-access | positive_impacts | response 212 (batch 1), proposed by coder_a, coder_b | alive |
| positive_impacts-problem_solving | positive_impacts | response 217 (batch 1), proposed by coder_a, coder_b | alive |
| positive_impacts-quality_of_life | positive_impacts | response 245 (batch 2), proposed by coder_a, coder_b | alive |
