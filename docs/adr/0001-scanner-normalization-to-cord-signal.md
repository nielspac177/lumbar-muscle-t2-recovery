# ADR 0001 — Normalize muscle T2 signal to spinal-cord signal

- **Status:** Accepted
- **Date:** 2026-07-08

## Context
Absolute T2 signal intensity on conventional (non-quantitative) MRI is not
comparable across scanners, coils, sequences, or scaling — the same muscle imaged
on two machines yields different raw intensities. Prior work associating raw
paraspinal T2 with outcomes therefore conflates muscle biology with acquisition
parameters. We need an intensity measure that is robust to these nuisance factors.

## Decision
For each muscle we compute a **cord-normalized T2 ratio** = (bilateral-mean muscle
mean intensity) / (spinal-cord mean intensity) on the same image
(`cleaning.build_muscle_exposures`, column `*_rcord`). Cerebrospinal-fluid-adjacent
cord is an internal reference present in every study; dividing by it cancels the
per-scan multiplicative scaling. The ratio is then z-scored within the cohort so
effects are reported per one standard deviation.

## Consequences
- Effects are interpretable across the heterogeneous scanner fleet in a
  retrospective registry.
- The ratio is dimensionless; the sign of the raw intensity–biology relationship
  is resolved empirically (`analysis.quality_direction`).
- Cord signal itself is assumed stable relative to muscle; pathologic cord signal
  (rare in this decompression cohort) would attenuate normalization — noted as a
  limitation.
- Alternative references (subcutaneous fat, CSF) are candidate sensitivity
  analyses (see `docs/STATS_VERIFICATION.md`).
