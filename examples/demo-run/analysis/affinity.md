## Affinity themes

11 of 14 codebook leaves clustered (3 excluded — see below). Blend: alpha * cosine(code_text) + (1 - alpha) * Jaccard(co-occurrence), alpha = 0.7, cut at similarity >= 0.5 (average linkage; PROVISIONAL, uncalibrated).

Naming a theme is a human act. `label_suggestion` below is mechanical — the most frequent name tokens among a group's members — and is not a proposed theme name.

> **Offline embedding space.** Offline similarity describes the fallback lexical embedder, not meaning (ADR-0019): the cosine component of the blend is lexical overlap here, and a cluster is a starting point for a human read, not a semantic claim.

### Groups

_No group of two or more leaves met the similarity threshold._

### Cross-family sub-codes

_No sub-code label is shared, identically, across more than one family._

### Singletons (11)

adoption-social_change, applications-automation, applications-data_driven_systems, applications-education, applications-healthcare, applications-industry_and_transport, future-imagined_scenario, negative_impacts-dependence, negative_impacts-job_loss, positive_impacts-problem_solving, positive_impacts-quality_of_life

### Excluded

| name | reason |
|---|---|
| applications-personalisation | not present in the occurrence matrix (filtered out, or never assigned) |
| future-uncertainty | not present in the occurrence matrix (filtered out, or never assigned) |
| positive_impacts-access | not present in the occurrence matrix (filtered out, or never assigned) |
