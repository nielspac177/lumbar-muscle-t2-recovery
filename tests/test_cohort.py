"""Unit tests for STROBE flow accounting in src/cohort.py."""
from __future__ import annotations

import numpy as np

from src.cohort import analytic_cohort, flow_counts


def test_flow_counts_are_monotone_nonincreasing(tidy_frame):
    fc = flow_counts(tidy_frame)
    seq = [fc["registry_rows"], fc["segmented"], fc["segmented_with_baseline_PF"],
           fc["segmented_with_1Y_PF"], fc["primary_complete_case"]]
    # each STROBE step can only lose or keep patients, never gain
    assert all(a >= b for a, b in zip(seq, seq[1:]))


def test_flow_counts_reflect_missingness(tidy_frame):
    df = tidy_frame.copy()
    df.loc[df.index[:5], "pf_1y"] = np.nan       # drop 5 one-year completers
    df.loc[df.index[:2], "iliopsoas_vol"] = np.nan  # de-segment 2
    fc = flow_counts(df)
    assert fc["registry_rows"] == len(df)
    assert fc["segmented"] == len(df) - 2
    assert fc["segmented_with_1Y_PF"] <= fc["segmented"] - 5 + 2  # bounded by drops


def test_analytic_cohort_is_complete_case(tidy_frame):
    coh = analytic_cohort(tidy_frame, "pf", "1y")
    for c in ["iliopsoas_vol", "pf_base", "pf_1y", "age", "sex"]:
        assert coh[c].notna().all()
