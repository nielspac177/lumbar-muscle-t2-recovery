"""Derived figure-input tables (WP-A4).

The publication figures (`src/figures_jama.py`) read only from ``results/*.csv``
so they are fully reproducible and never recompute statistics inline. This module
produces the two derived tables that the model-result CSVs do not already contain:
tertile MCID rates (with Wilson CIs) and the PROMIS-PF recovery trajectory by
heterogeneity group. Deterministic; no RNG.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MONTHS = {"base": 0.0, "6w": 1.5, "3m": 3.0, "6m": 6.0, "1y": 12.0, "2y": 24.0}
TERTILES = ["Low", "Intermediate", "High"]


def wilson(k: int, n: int):
    """Wilson score 95% CI for a proportion (analytic, no SciPy)."""
    if n == 0:
        return np.nan, np.nan, np.nan
    z = 1.959963985
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)


def tertile_mcid_rates(seg: pd.DataFrame, strat="z_iliopsoas_texture") -> pd.DataFrame:
    """% achieving ODI and PROMIS-PF MCID across iliopsoas-heterogeneity tertiles."""
    d = seg[seg[strat].notna()].copy()
    d["tertile"] = pd.qcut(d[strat], 3, labels=TERTILES)
    rows = []
    for outcome, flag in [("ODI", "odi_mcid_1y"), ("PROMIS-PF", "pf_mcid_1y")]:
        for t in TERTILES:
            s = d.loc[d["tertile"] == t, flag].dropna()
            p, lo, hi = wilson(int(s.sum()), len(s))
            rows.append({"strat": strat, "outcome": outcome, "tertile": t,
                         "k": int(s.sum()), "n": int(len(s)),
                         "pct": 100 * p, "lo": 100 * lo, "hi": 100 * hi})
    return pd.DataFrame(rows)


def pf_trajectory_by_heterogeneity(seg: pd.DataFrame,
                                   strat="z_iliopsoas_texture") -> pd.DataFrame:
    """Mean PROMIS-PF over time, split at the median of iliopsoas heterogeneity."""
    d = seg[seg[strat].notna()].copy()
    med = d[strat].median()
    d["grp"] = np.where(d[strat] >= med, "High heterogeneity", "Low heterogeneity")
    rows = []
    for grp, sub in d.groupby("grp"):
        for tp, mo in MONTHS.items():
            col = f"pf_{tp}"
            if col not in sub:
                continue
            v = sub[col].dropna()
            if len(v) >= 5:
                rows.append({"group": grp, "tp": tp, "month": mo,
                             "mean": float(v.mean()), "sem": float(v.sem()),
                             "n": int(len(v))})
    return pd.DataFrame(rows)


def build_figure_data(seg: pd.DataFrame) -> dict:
    """Return the derived figure tables keyed by output filename stem."""
    return {
        "tertile_mcid": tertile_mcid_rates(seg),
        "pf_trajectory": pf_trajectory_by_heterogeneity(seg),
    }
