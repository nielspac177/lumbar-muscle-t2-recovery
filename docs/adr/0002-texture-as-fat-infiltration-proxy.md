# ADR 0002 — Intramuscular T2 heterogeneity ("texture") as a fat-infiltration proxy

- **Status:** Accepted (exposure is **exploratory** — see ADR 0004)
- **Date:** 2026-07-08

## Context
Fatty infiltration streaks muscle with high-signal fat between fibres, increasing
the **heterogeneity** of intramuscular T2 signal. Quantitative fat-water (Dixon)
imaging was not available for this retrospective cohort, so we needed a proxy
computable from conventional T2 ROI statistics (mean, SD, percentiles, median).

## Decision
We derive two scanner-robust, dimensionless heterogeneity metrics per muscle
(`cleaning.build_muscle_exposures`):
- **Coefficient of variation** `*_cv` = SD / mean;
- **Normalized spread** `*_spread` = (p95 − p5) / median.

Because these correlate strongly (~0.9), we combine them into a single
consolidated exposure `z_*_texture` = **z(z_cv + z_spread)** — the two metrics are
each z-scored, summed, and the sum is re-standardized. Higher texture = more
heterogeneity = presumed more fatty infiltration.

## Consequences
- The consolidated texture is **double-standardized** (a z-score of a sum of
  z-scores). This is an asymmetry relative to `z_composite_voln`, which is the
  mean of z-scored volumes and is *not* re-standardized. This choice is documented
  and tested (`tests/test_cleaning.py::test_texture_is_zscore_of_summed_zscores`);
  a sensitivity analysis using CV alone and spread alone is reported in
  `docs/STATS_VERIFICATION.md`.
- Texture is a proxy, not a measurement, of fat fraction. The paper explicitly
  motivates prospective Dixon/fat-water imaging as the confirmatory step.
- The direction actually observed (higher preoperative T2 tracks *better*
  recovery) argues against chronic fat and toward reversible edema/inflammation;
  this reframing is central to the Discussion.
