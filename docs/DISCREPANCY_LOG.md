# Discrepancy log — WP-A1 corrections

Changes made during the independent statistical re-analysis, with their effect on
reported numbers. Per the study decision, code defects were **fixed autonomously**,
all outputs regenerated, and every changed number recorded here. The corrected
values are authoritative and are what the manuscript reports.

---

## D1 — Complete-case sample mis-specified in `mcid_logistic` (FIXED) ⚠ headline

**Defect.** `analysis.mcid_logistic` dropped incomplete cases on a **hard-coded
`pf_base`** column regardless of which baseline the model actually adjusted for:

```python
# before
d = df.dropna(subset=[flag, exposure, "age", "sex", "pf_base"]).copy()
```

For the ODI and Global-PH MCID models — whose baseline covariate is `odi_base` /
`ph_base` — this **wrongly excluded** patients who had the relevant outcome but a
missing PROMIS-PF baseline, shrinking the sample and biasing it toward PF
completers.

**Fix.** Define complete cases over the model's *own* variables
(`_formula_columns([flag, exposure, *covars])`), so each model uses exactly the
patients it needs.

**Effect on numbers:**

| Result | Before (buggy) | After (fixed) |
| --- | --- | --- |
| **ODI-MCID, iliopsoas heterogeneity** | OR 0.60 (0.40–0.91), p=0.015, n=108 | **OR 0.66 (0.45–0.96), p=0.031, n=120** |
| Global-PH MCID, iliopsoas heterogeneity | OR 1.06, p=0.75, n=123 | OR 1.18, p=0.35, n=140 |
| Global-PH threshold sweep (thr 3–5) | OR ≈0.92–1.06, p>0.6 | OR 1.03–1.18, p>0.34 |
| PROMIS-PF MCID, iliopsoas heterogeneity | OR 0.70, p=0.06, n=123 | **unchanged** (its baseline *is* pf_base) |

**Interpretation.** The direction and qualitative conclusion are unchanged: higher
preoperative iliopsoas T2 heterogeneity is associated with **lower** odds of
achieving the ODI MCID (exploratory), and this **does not replicate** across the
other instruments. The headline OR moves from 0.60 to **0.66** and remains
nominally significant (p=0.031). **This is the one headline-level number change and
is flagged for author sign-off.**

---

## D2 — Silent exception-swallowing hid dropped model cells (FIXED)

**Defect.** `mcid_table` and `t2_timecourse_table` wrapped each fit in
`except Exception: pass`, so a non-converging or degenerate cell vanished from the
output table with no trace, making the row count silently unreliable.

**Fix.** Replaced with a logged warning (`log.warning(...)`) naming the skipped
cell and reason. On the analytic data **no cells are skipped** — all 18 MCID cells
and all 16 time-course cells converge — so the published tables are complete; the
change only makes future degeneracy visible.

---

## D3 — Multiplicity not previously reported (ADDED)

**Gap.** The abstract reported raw p-values across 3 instruments × timepoints with
no family-wise control.

**Addition.** `src/robustness.py` now computes Holm and Benjamini–Hochberg FDR
within each pre-specified family (`results/robustness_table.csv`). The primary
3-month ODI effect survives correction (Holm/FDR p=0.043); the 1-year ODI effect
and the exploratory ODI-MCID heterogeneity are **nominal only**. This is now stated
explicitly in the manuscript — a strengthening, not a reversal.

---

## D4 — `texture` double-standardization documented + sensitivity added (RESOLVED)

**Concern.** `z_*_texture = z(z_cv + z_spread)` re-standardizes a sum of z-scores
(asymmetric with `z_composite_voln`, which is a plain mean of z-scores).

**Resolution.** Documented in ADR 0002 and locked by a unit test. A sensitivity
analysis (`robustness.headline_sensitivity`) shows the ODI-MCID result is
essentially identical using CV alone (OR 0.67, p=0.034) or normalized spread alone
(OR 0.65, p=0.034), so the double-standardization is **not** driving the finding.

---

## D5 — Adversarial-verification follow-ups (WP-A1 multi-agent pass)

An independent three-agent adversarial verification **reproduced the headline
OR = 0.6608 (0.45–0.96), p = 0.031, n = 120 exactly** (including a from-scratch
NumPy HC3 sandwich matching statsmodels to five decimals) and the primary
T2→ODI/PH effects. No estimate changed. It raised the following reporting fixes,
now applied:

- **Fragility.** The ODI-MCID result has a **fragility index of 1** (`results/fragility.csv`:
  one responder↔non-responder reassignment moves p from 0.031 to 0.19). Only 1 of
  18 MCID cells is nominally significant. Recorded, and the finding is described as
  hypothesis-generating throughout (ADR 0004).
- **Attrition is predominantly baseline-PRO missingness**, not 1-year loss to
  follow-up, and completers are a healthier subgroup (younger 60.8 vs 64.2 y
  p=0.015; lower baseline ODI 46.8 vs 53.9 p=0.027). A completer-vs-non-completer
  table **keyed on the ODI outcome** is now emitted
  (`results/attrition_odi.csv`); the previously shipped `attrition.csv` was keyed
  on PROMIS-PF completion. **Correction (WP-A7):** completion IS associated with
  the primary cord-normalized signal (iliopsoas rcord p=0.047) and mean intensity
  (p=0.004), though not with heterogeneity (p=0.10) or volume (p=0.65) — attrition
  is informative on exposure as well as outcome. IPW is now **actually implemented**
  (`robustness.ipw_headline` → `results/ipw_headline.csv`); the IPW-weighted
  ODI-MCID OR is 0.66 (0.46–0.96), p=0.031 — essentially identical to unweighted,
  so informative attrition on the modeled sample does not manufacture the
  association (an earlier draft asserted an unimplemented IPW with p≈0.01; that
  claim is corrected here to the computed p=0.031).
- **Multiplicity family pre-specified.** Families are **per PRO instrument**
  (each ODI and Global-PH time-course family = 2 muscles × 4 timepoints = 8 tests;
  the exploratory texture-MCID family = 3 muscles × 3 instruments = 9 tests). Under
  this pre-specification the primary 3-month ODI effect survives Holm/FDR (p=0.043).
  Disclosed sensitivity: pooling the two co-primary instruments into a single
  16-test family raises Holm to 0.080 (nominal) while FDR stays 0.043.
- **Provenance.** `ODI_MCID: 12.8` is now explicit in `config.yaml` /
  `config.example.yaml` (previously relied on the `cfg.get(..., 12.8)` default).
- **One row per patient.** The segmented cohort contains a few duplicate MRNs, but
  the analytic complete-case set (n=120) has none — noted for transparency.

## Items reviewed and left unchanged (no defect)

- **No RNG / seeds:** the estimation path is fully analytic; nothing to seed.
- **HC3 SE:** correctly applied to all OLS models (verified against classical SE in
  `tests/test_analysis.py`).
- **MCID flags NaN-safe:** `make_tidy` sets flags to NaN when either timepoint is
  missing (never silently 0) — confirmed.
- **`mmrm` dead code:** the mixed model is defined but unused by the pipeline; left
  in place for the optional companion analysis, noted here to avoid confusion.
