"""Unit tests for the exposure-construction logic in src/cleaning.py.

These lock the definitions of the scanner-robust exposures (cord-normalized T2,
coefficient of variation, normalized spread, consolidated texture) so that a
refactor cannot silently change what the manuscript reports.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.cleaning import build_muscle_exposures, compute_age, drop_implausible, normalize_sex


def test_rcord_is_mean_over_cord(raw_flat_frame):
    """z_*_rcord standardizes muscle-mean / spinal-cord-mean."""
    out = build_muscle_exposures(raw_flat_frame)
    cord = raw_flat_frame["Spinal cord | mean"]
    lmean = raw_flat_frame["left iliopsoas muscle | mean"]
    rmean = raw_flat_frame["right iliopsoas muscle | mean"]
    expected_ratio = ((lmean + rmean) / 2) / cord
    got_raw = out["iliopsoas_rcord"]
    # raw rcord must equal bilateral-mean intensity / cord signal
    assert np.allclose(got_raw, expected_ratio, rtol=1e-9)
    # z-scored column has ~zero mean and unit sd
    assert abs(out["z_iliopsoas_rcord"].mean()) < 1e-9
    assert abs(out["z_iliopsoas_rcord"].std(ddof=1) - 1.0) < 1e-9


def test_cv_is_sd_over_mean(raw_flat_frame):
    out = build_muscle_exposures(raw_flat_frame)
    lmean = raw_flat_frame["left iliopsoas muscle | mean"]
    rmean = raw_flat_frame["right iliopsoas muscle | mean"]
    lsd = raw_flat_frame["left iliopsoas muscle | sd"]
    rsd = raw_flat_frame["right iliopsoas muscle | sd"]
    expected = ((lsd + rsd) / 2) / ((lmean + rmean) / 2)
    assert np.allclose(out["iliopsoas_cv"], expected, rtol=1e-9)


def test_texture_is_zscore_of_summed_zscores(raw_flat_frame):
    """Documents the (double-standardized) texture definition: z(z_cv + z_spread)."""
    out = build_muscle_exposures(raw_flat_frame)
    combined = out["z_iliopsoas_cv"] + out["z_iliopsoas_spread"]
    z = (combined - combined.mean()) / combined.std()
    assert np.allclose(out["z_iliopsoas_texture"], z, rtol=1e-9, equal_nan=True)


def test_spine_normalized_volume(raw_flat_frame):
    out = build_muscle_exposures(raw_flat_frame)
    vert = drop_implausible(raw_flat_frame["Vertebra | Volume ( LM) cm3"])
    assert np.allclose(out["iliopsoas_voln"], out["iliopsoas_vol"] / vert,
                       rtol=1e-9, equal_nan=True)


def test_drop_implausible_removes_nonpositive_and_outliers():
    s = pd.Series([10.0, 11.0, 12.0, 9.0, -5.0, 0.0, 5000.0])
    out = drop_implausible(s)
    assert out.isna().sum() == 3  # the negative, the zero, and the huge outlier
    assert out.dropna().between(1, 100).all()


def test_normalize_sex_harmonizes_codings():
    data = pd.DataFrame({"gender": ["Male", "f", "FEMALE", "m", "unknown"]})
    out = normalize_sex(data)
    assert list(out) == ["male", "female", "female", "male", np.nan] or \
        (out.iloc[:4].tolist() == ["male", "female", "female", "male"]
         and pd.isna(out.iloc[4]))


def test_compute_age_bounds():
    data = pd.DataFrame({
        "dos": pd.to_datetime(["2020-01-01", "2020-01-01", "2020-01-01"]),
        "dob": pd.to_datetime(["1960-01-01", "2019-01-01", "1900-01-01"]),
    })
    age = compute_age(data)
    assert abs(age.iloc[0] - 60) < 0.1     # plausible
    assert pd.isna(age.iloc[1])            # age ~1 -> dropped (<18)
    assert pd.isna(age.iloc[2])            # age 120 -> dropped (>100)
