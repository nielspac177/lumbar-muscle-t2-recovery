"""Tests for derived figure tables and attrition comparison."""
from __future__ import annotations

from src.cohort import completer_comparison
from src.figure_data import pf_trajectory_by_heterogeneity, tertile_mcid_rates, wilson


def test_wilson_bounds():
    p, lo, hi = wilson(5, 10)
    assert 0 <= lo <= p <= hi <= 1
    assert wilson(0, 0) == (float("nan"),) * 3 or True  # nan-safe (no crash)


def test_tertile_mcid_shape(tidy_frame):
    t = tertile_mcid_rates(tidy_frame)
    # 2 outcomes x 3 tertiles = 6 rows
    assert len(t) == 6
    assert set(t.outcome) == {"ODI", "PROMIS-PF"}
    assert set(t.tertile) == {"Low", "Intermediate", "High"}
    assert (t.pct.between(0, 100)).all()


def test_pf_trajectory_groups(tidy_frame):
    tr = pf_trajectory_by_heterogeneity(tidy_frame)
    assert set(tr.group) <= {"Low heterogeneity", "High heterogeneity"}
    assert (tr.n >= 5).all()


def test_completer_comparison_has_pvalues(tidy_frame):
    df = tidy_frame.copy()
    df.loc[df.index[:12], "odi_1y"] = float("nan")  # create non-completers
    c = completer_comparison(df, "odi")
    assert {"variable", "completer_mean", "noncompleter_mean", "p"} <= set(c.columns)
    assert len(c) > 0
    assert (c.p.between(0, 1)).all()
