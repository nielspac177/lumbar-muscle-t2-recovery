# ADR 0004 — The T2-heterogeneity ("fat proxy") finding is exploratory

- **Status:** Accepted
- **Date:** 2026-07-08

## Context
The analysis tests two families of association: (1) the **primary** continuous
effect of cord-normalized T2 signal on functional recovery over time, and (2) an
**exploratory** contrast of muscle *size* (volume) versus muscle *quality*
(texture heterogeneity) on the odds of achieving each instrument's MCID at one
year. The heterogeneity→MCID result is significant for one instrument
(ODI-MCID: OR ≈ 0.60, p ≈ 0.015) but **does not replicate** across the other two
instruments (PROMIS-PF MCID OR ≈ 0.70, p ≈ 0.06; Global-PH MCID null), and the
Global-PH null is stable across improvement thresholds.

## Decision
The heterogeneity finding is designated **exploratory and hypothesis-generating**
and must be framed as such throughout the manuscript, figures, and abstract:
- it is reported alongside the non-replicating instruments, never in isolation;
- multiplicity across 3 instruments × timepoints is acknowledged, with FDR/Holm
  reported as sensitivity (`results/robustness_table.csv`);
- causal / "predictive" language is avoided for this contrast in favor of
  "associated with".

## Consequences
- Reviewers cannot reasonably accuse the paper of overselling a single-instrument,
  borderline result — the hedge is structural, not cosmetic.
- The cord-normalized-T2 association carries the paper. It is strongest and
  multiplicity-robust at 3 months; the 1-year association is nominal only (does not
  survive Holm correction) and must not be described as "durable." The
  cord-normalized-T2 analysis itself was developed post-hoc relative to the
  protocol's prespecified (null) volume analysis and is hypothesis-generating.
- The heterogeneity contrast motivates future quantitative fat-water imaging
  rather than claiming a fat-fraction effect; note that conventional T2 cannot
  separate fat from edema, so the tissue basis of the signal is unresolved.
- Enforced by the writing red-team pass (WP-A6) and the peer-review simulation
  (WP-A7).
