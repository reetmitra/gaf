# 15 - A seeded run: can the machine code into his organisation?

**This is a demonstration, not a result.** A seeded run starts from his codebook
instead of an empty one, so the machine codes *into his categories*. That makes it
the right way to ask "can this pipeline work inside an existing codebook" and the
wrong way to ask anything about agreement: a run that was handed the answer's
vocabulary is not independent evidence about that vocabulary (ADR-0035).

**ADR-0035's caveat applies to every number on this page.**

## The seed

| what | value |
|---|---|
| codebook | `runs/human200/codebook.json` |
| content hash | `f34339518689d9b4` |
| codes | 131 |
| families | 15 |
| codes carrying a definition | 131 |
| evidence rows held out | 312 |
| sources | `human-tagged`, `pi-codebook-md` |

**Held out means held out.** The seed arrives with the verified evidence his own
coding attached to it, and a seeded run must not count that evidence as its own work:
overlap between the seed's 312 evidence rows and the seeded run's
codebook evidence is **0**. Without the hold-out every number below would be
inflated by exactly that many occurrences.

## Cold against seeded, on the same corpus

| quantity | cold run | seeded run |
|---|---:|---:|
| n responses | 200 | 200 |
| assignments | 1952 | 1952 |
| codes final | 22 | 149 |
| families final | 6 | 16 |
| codes the run created itself | 22 | 18 |

Both runs write 1952 assignment rows and **186 of them differ**.
That is the mechanism working: given his categories the machine reached for one of
his where the cold run invented its own. It is also exactly why this run cannot be
quoted as agreement.
