# Statistical verification report (WP-A1)

Independent reproduction and adversarial stress-test of every statistic in the
fatproxy study. Companion files: [`NUMBERS_LEDGER.md`](NUMBERS_LEDGER.md) (number →
code → cell), [`DISCREPANCY_LOG.md`](DISCREPANCY_LOG.md) (defects fixed),
`results/robustness_table.csv` (multiplicity + sensitivity).

## Summary

- **All primary numbers reproduce exactly** from `python -m src.pipeline`: cohort
  n=385, age 62.8±13.3, 47% female; iliopsoas cord-normalized T2 → ΔGlobal-PH 3 mo
  β=+1.11 (0.54, 1.69); → ΔODI 3 mo β=−3.05; → ΔODI 1 y β=−2.40. Follow-up n and
  MCID rates (61%/67%) match.
- **One headline change** from a fixed complete-case bug: the exploratory ODI-MCID
  heterogeneity OR moved **0.60 → 0.66** (p 0.015 → 0.031); still significant, same
  direction, now on n=120 rather than 108 (see D1). Flagged for author sign-off.
- **The exploratory heterogeneity finding does not survive family-wise correction**
  (Holm/FDR p≈0.27–0.28), does not replicate across instruments, and has a
  **fragility index of 1** (one outcome reassignment flips significance) — the
  manuscript frames it as exploratory/hypothesis-generating throughout (ADR 0004).
- **Independently reproduced.** A three-agent adversarial pass re-derived the
  headline (OR 0.6608) and the primary effects with independent code, including a
  hand-coded HC3 sandwich matching statsmodels to five decimals; the estimates are
  not in question. Its recommendations (fragility, ODI-keyed attrition,
  per-instrument multiplicity family, config provenance) are applied — see
  `DISCREPANCY_LOG.md` D5.

## Design & assumptions checked

| Item | Finding |
| --- | --- |
| **Attrition (385 → analyzed)** | `results/attrition_odi.csv` compares 1-year ODI completers vs non-completers among the segmented cohort. Completion is **informative**: completers were younger (60.8 vs 64.2, p=.01), less disabled (ODI 46.8 vs 53.9, p=.03), and had higher iliopsoas cord-normalized signal (p=.047) and mean intensity (p=.004); heterogeneity (p=.10) and volume (p=.65) did not differ. Modeled samples are complete-case per outcome. Because attrition is on both outcome and the primary exposure, the headline was re-estimated with IPW. |
| **IPW for informative attrition** | `robustness.ipw_headline` → `results/ipw_headline.csv`. Stabilized inverse-probability-of-completion weights (completion modeled on age, sex, baseline ODI, exposure) leave the ODI-MCID heterogeneity result essentially unchanged: OR 0.66 (0.46–0.96), p=.031, vs unweighted 0.66. Does not address patients missing a baseline outcome. |
| **n reconciliation** | Outcome-available n (161/169) vs modeled complete-case n (118–140) reconciled in the ledger; manuscript reports the modeled n at each estimate. |
| **Multiplicity** | Holm + BH-FDR within pre-specified families (`robustness_table.csv`). Primary 3-mo ODI survives; 1-y ODI and exploratory MCID are nominal only. |
| **HC3 robust SE** | Applied to all OLS models; unit-tested to differ from classical SE (confirms `cov_type="HC3"` is active). |
| **Collinearity (T2 mean vs heterogeneity)** | Mean intensity (`rcord`) and heterogeneity (`texture`) are separate exposures in separate models, not co-entered, so mutual collinearity does not bias either estimate. |
| **Exposure operationalization** | Consolidated texture vs CV-alone vs spread-alone give the same ODI-MCID OR (0.65–0.67), so the double-standardization (ADR 0002) is not driving the result. |
| **Negative control** | Radicular leg-pain shows no association with any muscle exposure (all p ≥ 0.07): consistent with a decompression-governed outcome and argues against generic confounding. |
| **Determinism** | No RNG anywhere; two pipeline runs produce byte-identical `results/` (`make verify`). |

## Prespecified vs exploratory

- **Primary (confirmatory):** cord-normalized T2 signal → change in Global-PH and
  ODI over time, adjusted, per SD, HC3 SE.
- **Exploratory (hypothesis-generating):** muscle size vs heterogeneity → odds of
  achieving each instrument's MCID at 1 year. Multiplicity-corrected and reported
  as non-replicating.

## Open items / limitations (statistical)

1. Retrospective, single-center; attrition to 1 year is substantial (modeled n ≈
   120 of 385 segmented) — the durable 1-y effect is the most attrition-sensitive.
2. Conventional T2 heterogeneity is a **proxy** for fat/edema, not a measurement;
   quantitative fat–water (Dixon) imaging is the confirmatory next step.
3. The 1-year ODI effect and the exploratory MCID contrast are nominal under
   multiplicity control — stated plainly, not oversold.
