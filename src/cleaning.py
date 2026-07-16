"""Build the tidy, per-patient analysis frame and handle data-quality issues.

Implements the cleaning rules in PLAN.md §7:
  * age from dos - dob, computed from raw datetime components to tolerate
    out-of-range dates; restricted to a plausible 18-100 window;
  * sex harmonised across the mixed male/female/m/f coding;
  * implausible muscle and vertebral volumes set to missing (not winsorised),
    because the extreme values are segmentation errors rather than true extremes;
  * bilateral muscles combined (volume summed, quality volume-weighted);
  * spine-normalised volume index = muscle volume / vertebral-body volume;
  * exposures z-scored within the cohort so effects are per standard deviation.

BMI and number of levels are intentionally NOT used in the primary model
(see PLAN.md §4); helpers to derive a conservatively cleaned BMI are provided
for sensitivity analyses.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data_loading import col, col_exact

MUSCLES = {
    "iliopsoas": ("left iliopsoas muscle", "right iliopsoas muscle"),
    "deep_back": ("left deep back muscle", "right deep back muscle"),
    "glut_med": ("left gluteus medius", "right gluteus medius"),
}
VOL = "Volume ( LM) cm3"
QUAL = "mean"


def _num(s):
    return pd.to_numeric(s, errors="coerce") if s is not None else None


def _muscle_col(data, side_label, metric):
    """Fetch a numeric per-side metric, e.g. 'left iliopsoas muscle | mean'."""
    return _num(col(data, f"{side_label} | {metric}"))


def compute_age(data) -> pd.Series:
    """Age in years from date of surgery minus date of birth.

    Built from raw datetime objects to tolerate corrupted dates (e.g. year 2303)
    that overflow pandas Timestamps; implausible ages are set to missing.
    """
    dos, dob = col(data, "dos"), col(data, "dob")
    out = []
    for a, b in zip(dos, dob):
        try:
            out.append((a - b).days / 365.25 if pd.notna(a) and pd.notna(b) else np.nan)
        except Exception:
            out.append(np.nan)
    age = pd.Series(out, index=data.index)
    return age.where((age >= 18) & (age <= 100))


def normalize_sex(data) -> pd.Series:
    s = col(data, "gender").astype(str).str.strip().str.lower()
    return s.map({"male": "male", "m": "male", "female": "female", "f": "female"})


def drop_implausible(series: pd.Series) -> pd.Series:
    """Set non-positive values and extreme upper outliers (> Q3 + 3*IQR) to NaN."""
    s = series.copy()
    s = s.where(s > 0)
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    upper = q3 + 3 * (q3 - q1)
    return s.where(s <= upper)


def clean_bmi(data) -> pd.Series:
    """Conservatively harmonised BMI for SENSITIVITY use only.

    Weight is mixed kg/g and height mixed m/cm/mm; convert toward kg and cm,
    then keep only physiologically plausible values.
    """
    w = _num(col(data, "weight_kg"))
    h = _num(col(data, "height_cm"))
    w = w.where(w < 400, w / 1000.0)          # values in grams -> kg
    h = h.mask(h < 3, h * 100.0)              # metres -> cm
    h = h.mask(h > 250, h / 10.0)             # millimetres -> cm
    w = w.where((w >= 30) & (w <= 250))
    h = h.where((h >= 120) & (h <= 220))
    bmi = w / (h / 100.0) ** 2
    return bmi.where((bmi >= 12) & (bmi <= 70))


def _avg(a, b):
    """Bilateral mean of two per-side series (used for intensity-based metrics)."""
    return pd.concat([a, b], axis=1).mean(axis=1)


def build_muscle_exposures(data) -> pd.DataFrame:
    """Per-muscle bilateral exposures (z-scored): size and quality.

    Size:    volume, spine-normalised volume.
    Quality: mean intensity (crude), and two scanner-robust texture metrics that
             proxy fatty infiltration — coefficient of variation (SD/mean) and
             normalised spread ((p95-p5)/median); fatty streaking increases
             intramuscular heterogeneity. Because absolute MRI signal is not
             comparable across scans, texture (dimensionless) is preferred over
             raw mean. A consolidated `texture` z-score combines CV and spread
             (these correlate ~0.9), and a reference-normalised intensity
             (muscle mean / spinal-cord mean) is also provided.
    """
    vert = drop_implausible(_muscle_col(data, "Vertebra", VOL))
    cord = _muscle_col(data, "Spinal cord", QUAL)
    # Alternative internal references for the reference-sensitivity analysis: vertebral
    # marrow and intervertebral disc mean intensity. Unlike the central-canal ("cord")
    # reference — which sits in the compartment compressed by stenosis — these lie
    # outside the canal and let us test whether the primary association is an artifact
    # of the normalizing denominator (see robustness.reference_sensitivity).
    def _ref_or_nan(label):
        s = _muscle_col(data, label, QUAL)
        return s if s is not None else pd.Series(np.nan, index=data.index)
    vert_q = _ref_or_nan("Vertebra")
    disc_q = _ref_or_nan("intervertebral_discs")
    out = pd.DataFrame(index=data.index)
    out["vertebra_vol"] = vert
    out["cord_qual"] = cord
    out["vertebra_qual"] = vert_q
    out["disc_qual"] = disc_q
    for name, (l, r) in MUSCLES.items():
        lv = drop_implausible(_muscle_col(data, l, VOL))
        rv = drop_implausible(_muscle_col(data, r, VOL))
        total = lv.add(rv, fill_value=0).where(lv.notna() | rv.notna())
        mean = _avg(_muscle_col(data, l, QUAL), _muscle_col(data, r, QUAL))
        sd = _avg(_muscle_col(data, l, "sd"), _muscle_col(data, r, "sd"))
        p5 = _avg(_muscle_col(data, l, "percentil 5"), _muscle_col(data, r, "percentil 5"))
        p95 = _avg(_muscle_col(data, l, "percentil 95"), _muscle_col(data, r, "percentil 95"))
        med = _avg(_muscle_col(data, l, "median"), _muscle_col(data, r, "median"))
        out[f"{name}_vol"] = total
        out[f"{name}_voln"] = total / vert                       # spine-normalised
        out[f"{name}_qual"] = mean                               # crude quality
        out[f"{name}_cv"] = (sd / mean).replace([np.inf, -np.inf], np.nan)
        out[f"{name}_spread"] = ((p95 - p5) / med.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
        out[f"{name}_rcord"] = (mean / cord).replace([np.inf, -np.inf], np.nan)
        out[f"{name}_rvert"] = (mean / vert_q).replace([np.inf, -np.inf], np.nan)
        out[f"{name}_rdisc"] = (mean / disc_q).replace([np.inf, -np.inf], np.nan)

    def z(s):
        return (s - s.mean()) / s.std()

    for c in [c for c in out.columns if c != "vertebra_vol"]:
        out[f"z_{c}"] = z(out[c])
    # consolidated texture (CV + spread) per muscle; higher = more fatty infiltration
    for name in MUSCLES:
        out[f"z_{name}_texture"] = z(out[f"z_{name}_cv"] + out[f"z_{name}_spread"])
    out["z_composite_voln"] = out[[f"z_{m}_voln" for m in MUSCLES]].mean(axis=1)
    return out


# Outcome instruments and the timepoints we model
_OUTCOMES = {
    "pf": ("PROMIS Physical Function {tp} physical_function", "Physical Function {tp} physical_function"),
    "odi": ("Oswestry Disability Index {tp} oswestry_disability_index",),
    "back": ("Back Pain VAS {tp} back_pain_nrs",),
    "leg": ("Leg Pain VAS {tp} leg_pain_nrs",),
}
_TPS = {"base": "Baseline", "6w": "6W Post", "3m": "3M Post",
        "6m": "6M Post", "1y": "1Y Post", "2y": "2Y Post"}


def build_outcomes(data) -> pd.DataFrame:
    out = pd.DataFrame(index=data.index)
    for key, patterns in _OUTCOMES.items():
        for short, tp in _TPS.items():
            series = None
            for pat in patterns:
                series = _num(col(data, pat.format(tp=tp)))
                if series is not None:
                    break
            out[f"{key}_{short}"] = series
    # PROMIS Global-10 Physical Health (the group's primary instrument). Exact match
    # to avoid colliding with '..._raw_score' / '..._se' columns.
    for short, tp in _TPS.items():
        out[f"ph_{short}"] = _num(col_exact(
            data, f"PROMIS Global 10 {tp} global_physical_health"))
    return out


def make_tidy(data, cfg) -> pd.DataFrame:
    """Assemble the per-patient analysis frame from the raw workbook."""
    base = pd.DataFrame(index=data.index)
    base["mrn"] = col(data, "mrn")
    base["age"] = compute_age(data)
    base["sex"] = normalize_sex(data)
    base["num_level"] = _num(col(data, "num_level"))
    base["bmi"] = clean_bmi(data)
    tidy = pd.concat([base, build_muscle_exposures(data), build_outcomes(data)], axis=1)
    # MCID attainment (NaN where either timepoint is missing, never coerced to 0)
    pf_mcid = float(cfg.get("PROMIS_PF_MCID", 4.5))
    odi_mcid = float(cfg.get("ODI_MCID", 12.8))
    tidy["pf_mcid_1y"] = ((tidy["pf_1y"] - tidy["pf_base"]) >= pf_mcid).astype("float")
    tidy.loc[tidy["pf_1y"].isna() | tidy["pf_base"].isna(), "pf_mcid_1y"] = np.nan
    tidy["odi_mcid_1y"] = ((tidy["odi_base"] - tidy["odi_1y"]) >= odi_mcid).astype("float")
    tidy.loc[tidy["odi_1y"].isna() | tidy["odi_base"].isna(), "odi_mcid_1y"] = np.nan
    ph_mcid = float(cfg.get("GLOBAL_PH_MCID", 5.0))   # ~half-SD T-score improvement
    tidy["ph_mcid_1y"] = ((tidy["ph_1y"] - tidy["ph_base"]) >= ph_mcid).astype("float")
    tidy.loc[tidy["ph_1y"].isna() | tidy["ph_base"].isna(), "ph_mcid_1y"] = np.nan
    return tidy
