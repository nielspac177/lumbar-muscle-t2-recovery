# ADR 0003 — HC3 heteroskedasticity-robust standard errors

- **Status:** Accepted
- **Date:** 2026-07-08

## Context
The primary and secondary continuous models are ANCOVA-style OLS regressions of a
follow-up (or change) score on a standardized muscle exposure plus baseline, age,
and sex. Patient-reported outcome changes show non-constant variance (floor/ceiling
effects, baseline-dependent variance), which violates the homoskedasticity
assumption of classical OLS standard errors.

## Decision
All OLS models are fit with **HC3 heteroskedasticity-consistent standard errors**
(`statsmodels ... .fit(cov_type="HC3")`; see `analysis.ancova`,
`analysis.delta_adjusted`). HC3 is the recommended small-sample HC variant
(MacKinnon–White), more conservative than HC0–HC2 at the sample sizes here
(n ≈ 118–169 per model). Confidence intervals and p-values are read directly off
the HC3 covariance. The estimator is stated in every figure legend and Methods.

## Consequences
- Inference is valid under heteroskedasticity without modeling its form.
- HC3 is deterministic and analytic — no bootstrap — preserving bit-for-bit
  reproducibility (see `docs/ENVIRONMENT.md`).
- Observations are treated as independent. Because each patient contributes once
  per cross-sectional model, clustering is not required for the primary/secondary
  analyses; a cluster-robust sensitivity check is reported in
  `docs/STATS_VERIFICATION.md`.
- Logistic MCID models use standard maximum-likelihood SEs (robust SEs add little
  for a single binary outcome per patient); this is noted where reported.
