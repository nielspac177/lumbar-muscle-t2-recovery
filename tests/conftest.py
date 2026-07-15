"""Shared fixtures built from tiny hand-mocked frames.

No patient data is used anywhere in the test suite. The frames below are small,
synthetic, and constructed in code so the analysis package can be exercised
end-to-end without the (gitignored) source workbook.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

# The per-side intensity metrics that cleaning.build_muscle_exposures reads.
_METRICS = ["Volume ( LM) cm3", "mean", "sd", "percentil 5", "percentil 95", "median"]
_SIDES = {
    "iliopsoas": ("left iliopsoas muscle", "right iliopsoas muscle"),
    "deep_back": ("left deep back muscle", "right deep back muscle"),
    "glut_med": ("left gluteus medius", "right gluteus medius"),
}


@pytest.fixture
def raw_flat_frame():
    """A flattened 'group | metric' frame like data_loading.load_raw would emit.

    Deterministic, 24 synthetic rows, plausible magnitudes; enough spread that
    z-scores and correlations are well defined.
    """
    n = 24
    rng = np.random.default_rng(0)  # fixture-only RNG; the pipeline itself uses none
    cols = {}
    for muscle, (l, r) in _SIDES.items():
        for side in (l, r):
            cols[f"{side} | Volume ( LM) cm3"] = np.linspace(180, 320, n) + rng.normal(0, 5, n)
            cols[f"{side} | mean"] = np.linspace(40, 70, n) + rng.normal(0, 2, n)
            cols[f"{side} | sd"] = np.linspace(8, 18, n) + rng.normal(0, 1, n)
            cols[f"{side} | percentil 5"] = np.linspace(20, 35, n)
            cols[f"{side} | percentil 95"] = np.linspace(70, 110, n)
            cols[f"{side} | median"] = np.linspace(38, 68, n)
    cols["Vertebra | Volume ( LM) cm3"] = np.linspace(30, 45, n)
    cols["Spinal cord | mean"] = np.full(n, 100.0)
    return pd.DataFrame(cols)


@pytest.fixture
def tidy_frame():
    """A per-patient analysis frame with the exact z_/outcome columns the models use.

    40 patients, linear signal + noise, no missingness, so every model converges.
    """
    n = 40
    rng = np.random.default_rng(1)
    exp = rng.normal(0, 1, n)  # standardized exposure signal
    df = pd.DataFrame({
        "mrn": [f"MOCK{i:03d}" for i in range(n)],
        "age": rng.uniform(45, 80, n),
        "sex": rng.choice(["male", "female"], n),
        "iliopsoas_vol": rng.uniform(200, 320, n),
        "iliopsoas_qual": rng.uniform(40, 70, n),
    })
    for c in ["z_iliopsoas_rcord", "z_deep_back_rcord",
              "z_iliopsoas_voln", "z_deep_back_voln", "z_glut_med_voln",
              "z_composite_voln", "z_iliopsoas_qual", "z_deep_back_qual",
              "z_glut_med_qual", "z_iliopsoas_texture", "z_deep_back_texture",
              "z_glut_med_texture"]:
        df[c] = rng.normal(0, 1, n)
    df["z_iliopsoas_rcord"] = exp
    # Outcomes: baselines + follow-ups driven by the exposure so effects are nonzero.
    for out, sign in [("pf", 3.0), ("odi", -4.0), ("ph", 2.0), ("leg", 0.0),
                      ("back", -1.0)]:
        base = rng.uniform(20, 60, n)
        df[f"{out}_base"] = base
        for tp in ["6w", "3m", "6m", "1y"]:
            df[f"{out}_{tp}"] = base + sign * exp + rng.normal(0, 3, n)
    # MCID flags (NaN-safe like make_tidy)
    df["pf_mcid_1y"] = ((df["pf_1y"] - df["pf_base"]) >= 4.5).astype(float)
    df["odi_mcid_1y"] = ((df["odi_base"] - df["odi_1y"]) >= 12.8).astype(float)
    df["ph_mcid_1y"] = ((df["ph_1y"] - df["ph_base"]) >= 5.0).astype(float)
    return df
