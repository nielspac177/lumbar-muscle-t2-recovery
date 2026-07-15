"""Statistical models for the muscle-outcome study (PLAN.md §1, §5).

Primary analysis is ANCOVA: the one-year outcome regressed on a standardised
muscle exposure plus the baseline outcome, age, and sex, with HC3 robust standard
errors; effects are reported per one standard deviation of the exposure. A linear
mixed model over all timepoints provides an efficient, missingness-tolerant
companion analysis, and logistic regression models attainment of the MCID.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

log = logging.getLogger(__name__)

# Exposures of interest: spine-normalised volume and quality for each muscle,
# plus the composite volume score. Names match the z_ columns from cleaning.py.
EXPOSURES = [
    "z_iliopsoas_voln", "z_deep_back_voln", "z_glut_med_voln", "z_composite_voln",
    "z_iliopsoas_qual", "z_deep_back_qual", "z_glut_med_qual",
]
ADJUST = ["pf_base", "age", "C(sex)"]   # baseline replaced per-outcome in ancova()


def ancova(df, exposure, outcome="pf", timepoint="1y", covars=("age", "C(sex)")):
    """Fit `outcome_tp ~ exposure + outcome_base + covars` with HC3 SE.

    Returns a dict with the per-SD coefficient, 95% CI, p-value, and n.
    """
    y = f"{outcome}_{timepoint}"
    base = f"{outcome}_base"
    rhs = " + ".join([exposure, base, *covars])
    d = df.dropna(subset=[y, base, exposure, "age", "sex"]).copy()
    model = smf.ols(f"{y} ~ {rhs}", data=d).fit(cov_type="HC3")
    ci = model.conf_int().loc[exposure]
    return {
        "exposure": exposure, "outcome": outcome, "timepoint": timepoint,
        "n": int(model.nobs), "beta": float(model.params[exposure]),
        "ci_low": float(ci[0]), "ci_high": float(ci[1]),
        "p": float(model.pvalues[exposure]),
    }


# Exposures contrasted in the MCID figure: size (volume) vs quality (texture),
# for each muscle, plus the crude mean-intensity quality for reference.
MCID_EXPOSURES = [
    "z_iliopsoas_voln", "z_deep_back_voln", "z_glut_med_voln",
    "z_iliopsoas_texture", "z_deep_back_texture", "z_glut_med_texture",
]


def ph_mcid_threshold_sweep(df, exposure="z_iliopsoas_texture", thresholds=(3, 4, 5)):
    """Sensitivity: iliopsoas heterogeneity -> Global Physical Health MCID across
    improvement thresholds, confirming the null is threshold-independent."""
    rows = []
    for thr in thresholds:
        flag = ((df["ph_1y"] - df["ph_base"]) >= thr).astype(float)
        flag[df["ph_1y"].isna() | df["ph_base"].isna()] = np.nan
        d = df.assign(_phm=flag)
        r = mcid_logistic(d, exposure, flag="_phm", covars=("age", "C(sex)", "ph_base"))
        r["threshold"] = thr
        r["responder_rate"] = float(flag.mean())
        rows.append(r)
    return pd.DataFrame(rows)


def mcid_table(df: pd.DataFrame) -> pd.DataFrame:
    """Odds ratios for achieving MCID on ODI and PROMIS-PF at 1 year, per exposure.

    The headline contrast is muscle size (volume) versus muscle quality (texture).
    """
    rows = []
    specs = [("Global PH MCID (≥5)", "ph_mcid_1y", "ph_base"),
             ("ODI MCID (≥12.8)", "odi_mcid_1y", "odi_base"),
             ("PROMIS-PF MCID (≥4.5)", "pf_mcid_1y", "pf_base")]
    for model, flag, base in specs:
        for exp in MCID_EXPOSURES:
            try:
                r = mcid_logistic(df, exp, flag=flag, covars=("age", "C(sex)", base))
                r["model"] = model
                rows.append(r)
            except Exception as e:  # non-converging/degenerate cell — surface it
                log.warning("mcid_table skipped %s / %s: %s", model, exp, e)
    return pd.DataFrame(rows)


def _formula_columns(terms):
    """Raw dataframe columns referenced by a list of patsy formula terms.

    Strips the ``C(...)`` categorical wrapper so e.g. ``C(sex)`` -> ``sex``.
    Used to build a complete-case mask over exactly the model's own variables.
    """
    cols = []
    for t in terms:
        cols.append(t.replace("C(", "").replace(")", "").strip())
    return list(dict.fromkeys(cols))  # de-duplicated, order-preserving


def mcid_logistic(df, exposure, flag="pf_mcid_1y", covars=("age", "C(sex)", "pf_base")):
    """Logistic regression of MCID attainment on a standardised exposure.

    Complete cases are defined over the model's *own* variables (outcome flag,
    exposure, and each covariate incl. its baseline), so an ODI or Global-PH model
    is not incorrectly restricted to patients with a non-missing PROMIS-PF baseline.
    """
    rhs = " + ".join([exposure, *covars])
    d = df.dropna(subset=_formula_columns([flag, exposure, *covars])).copy()
    model = smf.logit(f"{flag} ~ {rhs}", data=d).fit(disp=0)
    ci = model.conf_int().loc[exposure]
    return {
        "exposure": exposure, "n": int(model.nobs),
        "or": float(np.exp(model.params[exposure])),
        "ci_low": float(np.exp(ci[0])), "ci_high": float(np.exp(ci[1])),
        "p": float(model.pvalues[exposure]),
    }


def mmrm(df, exposure, outcome="pf"):
    """Linear mixed model over all timepoints: efficient under MAR (PLAN.md §5).

    Long-format outcome with a categorical time factor, a random intercept per
    patient, and an exposure x time interaction. Returns the model summary frame.
    """
    tps = ["base", "6w", "3m", "6m", "1y", "2y"]
    long = df.melt(id_vars=["mrn", exposure, "age", "sex"],
                   value_vars=[f"{outcome}_{t}" for t in tps],
                   var_name="time", value_name="score")
    long["time"] = long["time"].str.replace(f"{outcome}_", "", regex=False)
    long = long.dropna(subset=["score", exposure, "mrn"])
    long["time"] = pd.Categorical(long["time"], categories=tps, ordered=True)
    md = smf.mixedlm(f"score ~ {exposure} * C(time) + age + C(sex)",
                     long, groups=long["mrn"])
    return md.fit(method="lbfgs", maxiter=200)


def run_all(cohort: pd.DataFrame) -> pd.DataFrame:
    """ANCOVA for every exposure on PROMIS-PF at 1Y plus the leg-pain negative
    control, assembled into one tidy results table for the JAMA forest figure."""
    rows = []
    for exp in EXPOSURES:
        rows.append({"model": "PF 1Y (ANCOVA)", **ancova(cohort, exp, "pf", "1y")})
    for exp in EXPOSURES:
        r = ancova(cohort, exp, "leg", "1y")
        r["model"] = "Leg pain 1Y (neg. control)"
        rows.append(r)
    return pd.DataFrame(rows)


# Primary (scanner-robust) exposures: T2 normalized to spinal-cord signal.
RATIO_EXP = {"z_iliopsoas_rcord": "Iliopsoas", "z_deep_back_rcord": "Deep back"}


def delta_adjusted(df, exposure, outcome, tp):
    """Adjusted regression of change in `outcome` (followup tp - baseline) on a
    standardised exposure + age + sex + baseline value, HC3 robust SE.
    Returns per-SD beta, 95% CI, p, n. (Improvement: PH increases, ODI decreases.)"""
    fu, base = f"{outcome}_{tp}", f"{outcome}_base"
    d = df.dropna(subset=[fu, base, exposure, "age", "sex"]).copy()
    d["_delta"] = d[fu] - d[base]
    mm = smf.ols(f"_delta ~ {exposure} + age + C(sex) + {base}", d).fit(cov_type="HC3")
    ci = mm.conf_int().loc[exposure]
    return {"exposure": exposure, "outcome": outcome, "tp": tp, "n": int(mm.nobs),
            "beta": float(mm.params[exposure]), "ci_low": float(ci[0]),
            "ci_high": float(ci[1]), "p": float(mm.pvalues[exposure])}


def t2_timecourse_table(df: pd.DataFrame) -> pd.DataFrame:
    """PRIMARY analysis: adjusted per-SD effect of cord-normalized T2 on change in
    PROMIS Global Physical Health and ODI across postoperative timepoints."""
    rows = []
    specs = [("Δ PROMIS Global Physical Health", "ph"),
             ("Δ Oswestry Disability Index", "odi")]
    for model, out in specs:
        for exp, mlabel in RATIO_EXP.items():
            for tp in ["6w", "3m", "6m", "1y"]:
                try:
                    r = delta_adjusted(df, exp, out, tp)
                    r["model"] = model
                    r["label"] = f"{mlabel} — {tp.upper()}"
                    rows.append(r)
                except Exception as e:  # surface a dropped timepoint cell
                    log.warning("t2_timecourse skipped %s %s %s: %s", out, exp, tp, e)
    return pd.DataFrame(rows)


def quality_direction(cohort: pd.DataFrame) -> pd.DataFrame:
    """Empirically resolve the sign of 'quality': correlate each muscle's raw
    intensity with age and with volume (older / atrophied -> more fat)."""
    rows = []
    for m in ("iliopsoas", "deep_back", "glut_med"):
        q = cohort[f"{m}_qual"]
        rows.append({
            "muscle": m,
            "corr_quality_age": cohort[["age"]].assign(q=q).corr().loc["age", "q"],
            "corr_quality_volume": cohort[[f"{m}_vol"]].assign(q=q).corr().iloc[0, 1],
        })
    return pd.DataFrame(rows)
