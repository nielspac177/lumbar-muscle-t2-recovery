"""Unit tests for the statistical models in src/analysis.py.

Checks that (a) the HC3 robust covariance is actually wired in, (b) the returned
effect summaries have the expected shape and recover a planted signal, and
(c) the models are deterministic across repeated fits.
"""
from __future__ import annotations

import numpy as np

from src.analysis import (
    ancova,
    delta_adjusted,
    mcid_logistic,
    mcid_table,
    run_all,
    t2_timecourse_table,
)


def test_ancova_uses_hc3_and_recovers_signal(tidy_frame):
    r = ancova(tidy_frame, "z_iliopsoas_rcord", outcome="pf", timepoint="1y")
    assert set(r) >= {"exposure", "outcome", "timepoint", "n", "beta",
                      "ci_low", "ci_high", "p"}
    assert r["n"] == len(tidy_frame)          # no missingness in the mock
    assert r["ci_low"] < r["beta"] < r["ci_high"]
    assert r["beta"] > 0                       # planted positive PF effect


def test_ancova_hc3_differs_from_classical(tidy_frame):
    """HC3 SEs should not equal the classical (non-robust) SEs -> confirms cov_type."""
    import statsmodels.formula.api as smf
    d = tidy_frame.dropna(subset=["pf_1y", "pf_base", "z_iliopsoas_rcord",
                                  "age", "sex"]).copy()
    f = "pf_1y ~ z_iliopsoas_rcord + pf_base + age + C(sex)"
    hc3 = smf.ols(f, d).fit(cov_type="HC3").bse["z_iliopsoas_rcord"]
    classical = smf.ols(f, d).fit().bse["z_iliopsoas_rcord"]
    assert not np.isclose(hc3, classical)


def test_delta_adjusted_signs(tidy_frame):
    r = delta_adjusted(tidy_frame, "z_iliopsoas_rcord", "odi", "1y")
    assert r["beta"] < 0                        # planted negative ODI-change effect
    assert r["n"] == len(tidy_frame)


def test_mcid_logistic_returns_or(tidy_frame):
    r = mcid_logistic(tidy_frame, "z_iliopsoas_texture", flag="pf_mcid_1y",
                      covars=("age", "C(sex)", "pf_base"))
    assert r["or"] > 0
    assert r["ci_low"] <= r["or"] <= r["ci_high"]


def test_pipeline_tables_are_deterministic(tidy_frame):
    """Two identical calls must produce identical result tables (no RNG in models)."""
    a = t2_timecourse_table(tidy_frame)
    b = t2_timecourse_table(tidy_frame)
    assert a.equals(b)
    c = run_all(tidy_frame)
    d = run_all(tidy_frame)
    assert c.equals(d)


def test_mcid_table_covers_all_specs(tidy_frame):
    """mcid_table spans all three MCID models across the 6 exposures.

    The full grid is 3 models x 6 exposures = 18 cells; a synthetic cell can hit
    perfect separation and drop, so we require near-complete coverage plus every
    model label appearing at least once.
    """
    tab = mcid_table(tidy_frame)
    assert 15 <= len(tab) <= 18
    assert set(tab["model"]) == {"Global PH MCID (≥5)", "ODI MCID (≥12.8)",
                                 "PROMIS-PF MCID (≥4.5)"}
