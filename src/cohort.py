"""Assemble the analytic cohort and report patient-flow counts (PLAN.md §3)."""
from __future__ import annotations

import pandas as pd
from scipy import stats

SEG_KEY = "iliopsoas_vol"      # presence of iliopsoas segmentation defines the imaged cohort


def flow_counts(tidy: pd.DataFrame) -> dict:
    """Counts at each STROBE step for the primary (PROMIS-PF at 1 year) analysis."""
    seg = tidy[SEG_KEY].notna()
    has_base = seg & tidy["pf_base"].notna()
    has_1y = has_base & tidy["pf_1y"].notna()
    cc = has_1y & tidy["age"].notna() & tidy["sex"].notna()
    return {
        "registry_rows": int(len(tidy)),
        "segmented": int(seg.sum()),
        "segmented_with_baseline_PF": int(has_base.sum()),
        "segmented_with_1Y_PF": int(has_1y.sum()),
        "primary_complete_case": int(cc.sum()),
    }


def completers_vs_noncompleters(tidy: pd.DataFrame) -> pd.DataFrame:
    """Compare baseline characteristics of 1Y completers vs non-completers
    among the segmented cohort, to assess attrition bias."""
    seg = tidy[tidy[SEG_KEY].notna()].copy()
    seg["completer_1y"] = seg["pf_1y"].notna()
    cols = ["age", "pf_base", "odi_base", "leg_base", "iliopsoas_vol", "iliopsoas_qual"]
    return seg.groupby("completer_1y")[cols].agg(["mean", "count"]).T


def completer_comparison(tidy: pd.DataFrame, outcome="odi") -> pd.DataFrame:
    """Tidy completer-vs-non-completer baseline table for a given outcome's 1-year
    follow-up, with a two-sample test per characteristic (attrition-bias check).

    "Completer" = segmented patient with a non-missing 1-year value of `outcome`.
    Continuous vars use Welch's t-test; sex uses a chi-square test. This lets the
    manuscript report attrition stratified by the ODI outcome that carries the
    exploratory finding, not only by PROMIS-PF.
    """
    seg = tidy[tidy[SEG_KEY].notna()].copy()
    comp = seg[f"{outcome}_1y"].notna()
    rows = []
    cont = ["age", "pf_base", "odi_base", "leg_base", "iliopsoas_vol",
            "iliopsoas_qual", "iliopsoas_rcord", "z_iliopsoas_texture"]
    for c in cont:
        if c not in seg:
            continue
        a = seg.loc[comp, c].dropna()
        b = seg.loc[~comp, c].dropna()
        if len(a) < 3 or len(b) < 3:
            continue
        p = float(stats.ttest_ind(a, b, equal_var=False).pvalue)
        rows.append({"variable": c, "completer_mean": round(float(a.mean()), 3),
                     "completer_n": int(len(a)),
                     "noncompleter_mean": round(float(b.mean()), 3),
                     "noncompleter_n": int(len(b)), "p": round(p, 4)})
    # sex (chi-square on the 2x2)
    if "sex" in seg:
        tab = pd.crosstab(comp, seg["sex"])
        if tab.shape == (2, 2) and tab.values.min() > 0:
            p = float(stats.chi2_contingency(tab)[1])
            fem = seg["sex"].eq("female")
            rows.append({"variable": "female",
                         "completer_mean": round(float(fem[comp].mean()), 3),
                         "completer_n": int(comp.sum()),
                         "noncompleter_mean": round(float(fem[~comp].mean()), 3),
                         "noncompleter_n": int((~comp).sum()), "p": round(p, 4)})
    out = pd.DataFrame(rows)
    out.insert(0, "outcome", outcome)
    return out


def analytic_cohort(tidy: pd.DataFrame, outcome="pf", timepoint="1y") -> pd.DataFrame:
    """Rows with imaging plus baseline and the requested follow-up of `outcome`."""
    need = [SEG_KEY, f"{outcome}_base", f"{outcome}_{timepoint}", "age", "sex"]
    return tidy[tidy[need].notna().all(axis=1)].copy()
