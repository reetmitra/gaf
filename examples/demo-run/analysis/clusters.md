## Ward's hierarchical cluster analysis

14 responses x 11 codes; 1 clusters (derived from the agglomeration schedule).

> **Read this before quoting the cluster count.**
>
> - the largest break is at stage 13 of 13, so the Essary rule gives 1 cluster(s); the data does not support a cluster structure at this sample size — set AnalysisConfig.n_clusters explicitly if a partition is wanted anyway.

| cluster | n | share | prominent codes (mean >= 0.4) |
|---:|---:|---:|---|
| 1 | 14 | 100% | future-imagined_scenario (0.64), adoption-social_change (0.57) |

### Cluster 1 — code means (top 10)

| code | mean | responses |
|---|---:|---:|
| future-imagined_scenario | **0.643** | 9 |
| adoption-social_change | **0.571** | 8 |
| applications-data_driven_systems | 0.214 | 3 |
| applications-industry_and_transport | 0.214 | 3 |
| negative_impacts-dependence | 0.214 | 3 |
| negative_impacts-job_loss | 0.214 | 3 |
| positive_impacts-problem_solving | 0.214 | 3 |
| applications-automation | 0.143 | 2 |
| applications-education | 0.143 | 2 |
| applications-healthcare | 0.143 | 2 |

Agglomeration schedule — 13 merge steps over 14 responses. Largest break at stage 13 (delta 0.7657) -> 14 - 13 = 1 clusters.

| stage | coefficient | change | cluster size |
|---:|---:|---:|---:|
| 1 | 1.0000 | 0.0000 | 2 |
| 2 | 1.0000 | 0.0000 | 2 |
| 3 | 1.2910 | 0.2910 | 3 |
| 4 | 1.4142 | 0.1232 | 2 |
| 5 | 1.4142 | 0.0000 | 2 |
| 6 | 1.4142 | 0.0000 | 2 |
| 7 | 1.4142 | 0.0000 | 3 |
| 8 | 2.0000 | 0.5858 | 2 |
| 9 | 2.1213 | 0.1213 | 4 |
| 10 | 2.3664 | 0.2451 | 5 |
| 11 | 2.4833 | 0.1168 | 6 |
| 12 | 2.6458 | 0.1625 | 9 |
| 13 | 3.4115 | 0.7657 **<- break** | 14 |

> **Warning.** the largest break is at stage 13 of 13, so the Essary rule gives 1 cluster(s); the data does not support a cluster structure at this sample size — set AnalysisConfig.n_clusters explicitly if a partition is wanted anyway.

> **Warning.** the largest break is at stage 13 of 13, so the Essary rule gives 1 cluster(s); the data does not support a cluster structure at this sample size — set AnalysisConfig.n_clusters explicitly if a partition is wanted anyway.
