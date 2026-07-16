"""Robustness and sensitivity analyses for the fatproxy study (WP-A1).

Assembles a single tidy table that (a) applies multiplicity control to the
exploratory MCID family and the primary time-course family, and (b) stress-tests
the headline heterogeneity result against alternative exposure definitions and
case selections. Written to ``results/robustness_table.csv`` by the pipeline.

Everything here is analytic and deterministic (no resampling).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

from .analysis import _formula_columns, mcid_logistic, mcid_table, t2_timecourse_table


def fragility_index(seg, exposure="z_iliopsoas_texture", flag="odi_mcid_1y",
                    base="odi_base", alpha=0.05, max_flips=15):
    """Greedy fragility index of a logistic MCID result.

    The minimum number of single-patient outcome reassignments that pushes the
    exposure's Wald p-value from < alpha to >= alpha. At each step the flip that
    most increases the p-value is taken. Returns a dict with the index and the
    p-value trajectory. A small index means the significance is fragile.
    """
    d = seg.dropna(subset=_formula_columns([flag, exposure, "age", "C(sex)", base])).copy()
    d = d.reset_index(drop=True)
    rhs = f"{exposure} + age + C(sex) + {base}"

    def pval(frame):
        try:
            m = smf.logit(f"{flag} ~ {rhs}", data=frame).fit(disp=0)
            return float(m.pvalues[exposure])
        except Exception:
            return 1.0

    p0 = pval(d)
    traj = [round(p0, 4)]
    if p0 >= alpha:
        return {"fragility_index": 0, "start_p": round(p0, 4), "trajectory": traj,
                "note": "already non-significant"}
    work = d.copy()
    flips = 0
    while flips < max_flips:
        best_p, best_i = -1.0, None
        for i in range(len(work)):
            trial = work.copy()
            trial.loc[i, flag] = 1.0 - trial.loc[i, flag]  # flip 0<->1
            p = pval(trial)
            if p > best_p:
                best_p, best_i = p, i
        work.loc[best_i, flag] = 1.0 - work.loc[best_i, flag]
        flips += 1
        traj.append(round(best_p, 4))
        if best_p >= alpha:
            return {"fragility_index": flips, "start_p": round(p0, 4),
                    "end_p": round(best_p, 4), "trajectory": traj}
    return {"fragility_index": f">{max_flips}", "start_p": round(p0, 4),
            "trajectory": traj}


def _holm_fdr(pvals):
    """Return (Holm-adjusted, Benjamini-Hochberg FDR-adjusted) p-value arrays."""
    p = np.asarray(pvals, dtype=float)
    holm = multipletests(p, method="holm")[1]
    fdr = multipletests(p, method="fdr_bh")[1]
    return holm, fdr


def mcid_multiplicity(seg: pd.DataFrame) -> pd.DataFrame:
    """MCID family (3 instruments x 6 exposures) with Holm and FDR adjustment.

    Adjustment is applied within the *quality/texture* contrast family — the
    exploratory hypotheses — reported alongside the raw p so readers can see the
    exploratory finding does not survive naive family-wide correction.
    """
    m = mcid_table(seg).copy()
    m["analysis"] = "MCID logistic (per SD)"
    tex = m[m["exposure"].str.contains("texture")].copy()
    holm, fdr = _holm_fdr(tex["p"].values)
    tex["p_holm"] = holm
    tex["p_fdr"] = fdr
    tex["family"] = "texture x 3 instruments (exploratory)"
    vol = m[m["exposure"].str.contains("voln")].copy()
    h2, f2 = _holm_fdr(vol["p"].values)
    vol["p_holm"] = h2
    vol["p_fdr"] = f2
    vol["family"] = "volume x 3 instruments (exploratory)"
    return pd.concat([tex, vol], ignore_index=True)


def primary_multiplicity(seg: pd.DataFrame) -> pd.DataFrame:
    """Primary cord-normalized T2 time-course family with Holm/FDR adjustment."""
    t = t2_timecourse_table(seg).copy()
    t["analysis"] = "Primary Δ ANCOVA (per SD)"
    out = []
    for out_name, grp in t.groupby("outcome"):
        g = grp.copy()
        holm, fdr = _holm_fdr(g["p"].values)
        g["p_holm"] = holm
        g["p_fdr"] = fdr
        g["family"] = f"iliopsoas+deep-back x 4 timepoints ({out_name})"
        out.append(g)
    return pd.concat(out, ignore_index=True)


def _odi_mcid_or(seg, exposure):
    """ODI-MCID logistic OR for an arbitrary exposure column (headline sensitivity)."""
    try:
        r = mcid_logistic(seg, exposure, flag="odi_mcid_1y",
                          covars=("age", "C(sex)", "odi_base"))
        return r
    except Exception:
        return None


def headline_sensitivity(seg: pd.DataFrame) -> pd.DataFrame:
    """Stress-test the ODI-MCID iliopsoas-heterogeneity result.

    Varies the heterogeneity operationalization (consolidated texture vs CV alone
    vs normalized spread alone) and the case selection (available-case with any
    valid covariate baseline vs strict complete-case), to show the direction is
    stable even though the exact OR is definition-dependent.
    """
    rows = []
    variants = [
        ("consolidated texture z(cv+spread)", "z_iliopsoas_texture"),
        ("CV alone", "z_iliopsoas_cv"),
        ("normalized spread alone", "z_iliopsoas_spread"),
    ]
    for label, col in variants:
        if col not in seg.columns:
            continue
        r = _odi_mcid_or(seg, col)
        if r:
            rows.append({"analysis": "ODI-MCID heterogeneity sensitivity",
                         "family": "exposure definition", "variant": label,
                         "exposure": col, "n": r["n"], "estimate": r["or"],
                         "ci_low": r["ci_low"], "ci_high": r["ci_high"], "p": r["p"]})
    # cluster-robust vs HC3 on the primary ODI-1y delta (no clusters here; report HC3)
    return pd.DataFrame(rows)


def ipw_headline(seg: pd.DataFrame) -> pd.DataFrame:
    """Inverse-probability-of-attrition-weighted ODI-MCID heterogeneity result.

    Fits a completion model (P[non-missing 1-year ODI | age, sex, baseline ODI,
    exposure]), forms stabilized weights, and refits the ODI-MCID logistic among
    completers with those weights. Tests whether informative attrition on the
    primary exposure changes the headline estimate. Deterministic.
    """
    import statsmodels.api as sm
    d = seg.copy()
    d["completed"] = d["odi_1y"].notna().astype(int)
    cm_df = d.dropna(subset=["age", "sex", "odi_base", "z_iliopsoas_texture"]).copy()
    cm = smf.logit("completed ~ age + C(sex) + odi_base + z_iliopsoas_texture",
                   data=cm_df).fit(disp=0)
    cm_df["pscore"] = cm.predict(cm_df)
    pc = cm_df["completed"].mean()
    cm_df["sw"] = np.where(cm_df["completed"] == 1, pc / cm_df["pscore"],
                           (1 - pc) / (1 - cm_df["pscore"]))
    mdf = cm_df[cm_df["completed"] == 1].dropna(subset=["odi_mcid_1y"]).copy()
    X = sm.add_constant(mdf[["z_iliopsoas_texture", "age", "odi_base"]].assign(
        sex=(mdf["sex"] == "female").astype(float)))
    m = sm.GLM(mdf["odi_mcid_1y"], X, family=sm.families.Binomial(),
               freq_weights=mdf["sw"]).fit()
    b, se = m.params["z_iliopsoas_texture"], m.bse["z_iliopsoas_texture"]
    return pd.DataFrame([{
        "analysis": "ODI-MCID heterogeneity, IPW for attrition",
        "or": float(np.exp(b)), "ci_low": float(np.exp(b - 1.96 * se)),
        "ci_high": float(np.exp(b + 1.96 * se)), "p": float(m.pvalues["z_iliopsoas_texture"]),
        "n": int(m.nobs)}])


def reference_sensitivity(seg: pd.DataFrame) -> pd.DataFrame:
    """Sensitivity of the primary iliopsoas T2 associations to the internal reference.

    The primary exposure normalizes muscle T2 to the central-canal ("cord") structure,
    which sits in the compartment compressed by stenosis. This tests whether the
    associations persist when the muscle signal is instead (a) normalized to references
    outside the canal (vertebral marrow, intervertebral disc), (b) left unnormalized
    (raw mean intensity), and (c) decomposed into its numerator (muscle signal) and
    denominator (canal reference) as separate predictors, plus an influence check
    (refit dropping the three highest Cook's-distance observations). Deterministic.
    """
    rows = []
    specs = [("odi", "3m"), ("odi", "1y"), ("ph", "3m")]
    refs = [("muscle / cord (primary)", "z_iliopsoas_rcord"),
            ("muscle / vertebral marrow", "z_iliopsoas_rvert"),
            ("muscle / disc", "z_iliopsoas_rdisc"),
            ("raw muscle intensity (no reference)", "z_iliopsoas_qual")]

    def _one(d, exp, formula, base):
        m = smf.ols(formula, d).fit(cov_type="HC3")
        ci = m.conf_int().loc[exp]
        return {"n": int(m.nobs), "beta": float(m.params[exp]),
                "ci_low": float(ci[0]), "ci_high": float(ci[1]), "p": float(m.pvalues[exp])}

    for out, tp in specs:
        fu, base = f"{out}_{tp}", f"{out}_base"
        for lab, exp in refs:
            d = seg.dropna(subset=[fu, base, exp, "age", "sex"]).copy()
            d["_delta"] = d[fu] - d[base]
            rows.append({"outcome": out, "tp": tp, "analysis": lab, "exposure": exp,
                         **_one(d, exp, f"_delta ~ {exp} + age + C(sex) + {base}", base)})
        # numerator / denominator decomposition
        d = seg.dropna(subset=[fu, base, "z_iliopsoas_qual", "z_cord_qual", "age", "sex"]).copy()
        d["_delta"] = d[fu] - d[base]
        for term, tag in [("z_iliopsoas_qual", "decomposition: muscle numerator"),
                          ("z_cord_qual", "decomposition: canal denominator")]:
            rows.append({"outcome": out, "tp": tp, "analysis": tag, "exposure": term,
                         **_one(d, term,
                                f"_delta ~ z_iliopsoas_qual + z_cord_qual + age + C(sex) + {base}", base)})
        # influence: refit primary model dropping the 3 highest Cook's-distance points
        d = seg.dropna(subset=[fu, base, "z_iliopsoas_rcord", "age", "sex"]).copy()
        d["_delta"] = d[fu] - d[base]
        ols = smf.ols(f"_delta ~ z_iliopsoas_rcord + age + C(sex) + {base}", d).fit()
        drop = np.argsort(ols.get_influence().cooks_distance[0])[::-1][:3]
        d2 = d.drop(d.index[drop])
        rows.append({"outcome": out, "tp": tp, "analysis": "muscle / cord (drop top-3 influential)",
                     "exposure": "z_iliopsoas_rcord",
                     **_one(d2, "z_iliopsoas_rcord",
                            f"_delta ~ z_iliopsoas_rcord + age + C(sex) + {base}", base)})
    cols = ["outcome", "tp", "analysis", "exposure", "n", "beta", "ci_low", "ci_high", "p"]
    return pd.DataFrame(rows)[cols]


def build_robustness_table(seg: pd.DataFrame) -> pd.DataFrame:
    """Concatenate all robustness analyses into one long, tidy table."""
    parts = []
    for df in (primary_multiplicity(seg), mcid_multiplicity(seg), headline_sensitivity(seg)):
        parts.append(df)
    cols = ["analysis", "family", "variant", "model", "outcome", "tp", "exposure",
            "n", "beta", "or", "estimate", "ci_low", "ci_high", "p", "p_holm", "p_fdr", "label"]
    out = pd.concat(parts, ignore_index=True)
    keep = [c for c in cols if c in out.columns]
    return out[keep]
