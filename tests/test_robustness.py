"""Tests for the robustness/multiplicity helpers in src/robustness.py."""
from __future__ import annotations

import numpy as np

from src.robustness import _holm_fdr, build_robustness_table, mcid_multiplicity


def test_holm_fdr_monotone_and_bounded():
    p = [0.001, 0.02, 0.04, 0.5]
    holm, fdr = _holm_fdr(p)
    # adjusted p-values are >= raw and <= 1
    assert np.all(holm >= np.array(p) - 1e-12)
    assert np.all(fdr >= np.array(p) - 1e-12)
    assert np.all(holm <= 1.0) and np.all(fdr <= 1.0)


def test_mcid_multiplicity_adds_adjusted_columns(tidy_frame):
    m = mcid_multiplicity(tidy_frame)
    for c in ("p", "p_holm", "p_fdr", "family"):
        assert c in m.columns
    # adjusted never smaller than raw within a family
    assert (m["p_holm"] >= m["p"] - 1e-9).all()


def test_build_robustness_table_is_deterministic(tidy_frame):
    a = build_robustness_table(tidy_frame)
    b = build_robustness_table(tidy_frame)
    assert a.equals(b)
    assert len(a) > 0
