"""JAMA-style forest tables with crude and adjusted columns (WP figures).

Renders the classic JAMA table+forest layout: grouped rows with banded section
headers, a No. column, and — side by side — a **crude** forest panel with its
numeric estimate (95% CI) and an **adjusted** forest panel with its estimate,
followed by a footnote naming the adjustment covariates.

Data builders compute crude (exposure-only) and adjusted (+ age, sex, baseline)
estimates for the continuous change models (β) and the MCID models (OR); both are
deterministic and reuse the same complete-case rule as `src/analysis.py`.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.formula.api as smf

from .theme import JAMA, apply_jama_style, save_all


# --------------------------------------------------------------------------- data
def _beta(df, exposure, outcome, tp, adjust):
    fu, base = f"{outcome}_{tp}", f"{outcome}_base"
    d = df.dropna(subset=[fu, base, exposure, "age", "sex"]).copy()
    d["_delta"] = d[fu] - d[base]
    rhs = exposure + (f" + age + C(sex) + {base}" if adjust else "")
    m = smf.ols(f"_delta ~ {rhs}", d).fit(cov_type="HC3")
    ci = m.conf_int().loc[exposure]
    return {"n": int(m.nobs), "est": float(m.params[exposure]),
            "lo": float(ci[0]), "hi": float(ci[1]), "p": float(m.pvalues[exposure])}


def _or(df, exposure, flag, base, adjust):
    cov = f" + age + C(sex) + {base}" if adjust else ""
    d = df.dropna(subset=[flag, exposure, "age", "sex", base]).copy()
    m = smf.logit(f"{flag} ~ {exposure}{cov}", d).fit(disp=0)
    ci = m.conf_int().loc[exposure]
    return {"n": int(m.nobs), "est": float(np.exp(m.params[exposure])),
            "lo": float(np.exp(ci[0])), "hi": float(np.exp(ci[1])),
            "p": float(m.pvalues[exposure])}


def build_primary_beta(seg):
    """Rows for the primary cord-normalized T2 -> change analysis (β scale)."""
    rows = []
    tps = [("6w", "6 wk"), ("3m", "3 mo"), ("6m", "6 mo"), ("1y", "1 yr")]
    muscles = [("z_iliopsoas_rcord", "Iliopsoas"), ("z_deep_back_rcord", "Deep back")]
    for out, gname in [("odi", "Δ Oswestry Disability Index"),
                       ("ph", "Δ PROMIS Global Physical Health")]:
        rows.append({"group": gname})
        for exp, mlabel in muscles:
            for tp, tlabel in tps:
                c = _beta(seg, exp, out, tp, False)
                a = _beta(seg, exp, out, tp, True)
                rows.append({"label": f"{mlabel}, {tlabel}", "n": a["n"],
                             "crude": c, "adj": a})
    return rows


def build_mcid_or(seg):
    """Rows for the exploratory size-vs-heterogeneity -> MCID analysis (OR scale)."""
    rows = []
    specs = [("odi_mcid_1y", "odi_base", "ODI MCID (≥12.8)"),
             ("pf_mcid_1y", "pf_base", "PROMIS-PF MCID (≥4.5)"),
             ("ph_mcid_1y", "ph_base", "Global PH MCID (≥5)")]
    exps = [("z_iliopsoas_voln", "Iliopsoas volume"),
            ("z_iliopsoas_texture", "Iliopsoas heterogeneity")]
    for flag, base, gname in specs:
        rows.append({"group": gname})
        for exp, elabel in exps:
            c = _or(seg, exp, flag, base, False)
            a = _or(seg, exp, flag, base, True)
            rows.append({"label": elabel, "n": a["n"], "crude": c, "adj": a})
    return rows


# ------------------------------------------------------------------------- render
def _fmt(est, lo, hi):
    return f"{est:.2f} ({lo:.2f} to {hi:.2f})"


def _fmt_p(p):
    if p < 0.001:
        return "<.001"
    return f"{p:.3f}".lstrip("0") if p < 1 else f"{p:.2f}"


def jama_forest_table(rows, scale="or", out="figures/forest_table",
                      title="", xlabel="", favors=("Favors lower", "Favors higher"),
                      covariate_note="", xticks=None, xlim=None):
    """Render a crude|adjusted JAMA forest table.

    `rows` is a list of dicts; a dict with only 'group' starts a banded section,
    otherwise it has 'label', 'n', 'crude', 'adj' (each est/lo/hi/p). `scale` is
    'or' (log axis, ref 1) or 'beta' (linear, ref 0).
    """
    apply_jama_style()
    ref = 1.0 if scale == "or" else 0.0
    n_slots = len(rows)
    row_h = 0.34
    # Fixed vertical overhead (inches) so the header and footnote hug the table
    # instead of leaving a margin that grows with the row count.
    top_ovh, bot_ovh = 1.05, 0.82
    fig_h = top_ovh + bot_ovh + n_slots * row_h
    fig = plt.figure(figsize=(9.2, fig_h))
    top_frac = (fig_h - top_ovh) / fig_h
    bottom_frac = bot_ovh / fig_h
    hy = (fig_h - 0.86) / fig_h          # column-header baseline
    top_rule_y = (fig_h - 0.70) / fig_h  # heavy top rule
    title_y = (fig_h - 0.42) / fig_h
    xlabel_y = 0.30 / fig_h
    note_y = 0.10 / fig_h

    # 5 columns: labels | crude forest | crude text | adj forest | adj text
    gs = fig.add_gridspec(1, 5, width_ratios=[3.0, 2.0, 1.7, 2.0, 1.7],
                          wspace=0.04, left=0.02, right=0.985,
                          top=top_frac, bottom=bottom_frac)
    ax_lab = fig.add_subplot(gs[0]); ax_c = fig.add_subplot(gs[1])
    ax_ct = fig.add_subplot(gs[2]); ax_a = fig.add_subplot(gs[3])
    ax_at = fig.add_subplot(gs[4])
    forests = [ax_c, ax_a]

    y = np.arange(n_slots)[::-1]  # top row highest y
    for ax in [ax_lab, ax_c, ax_ct, ax_a, ax_at]:
        ax.set_ylim(-0.6, n_slots - 0.4)
        ax.axis("off")

    # data range for forests
    all_lo = [r["crude"]["lo"] for r in rows if "crude" in r] + \
             [r["adj"]["lo"] for r in rows if "adj" in r]
    all_hi = [r["crude"]["hi"] for r in rows if "crude" in r] + \
             [r["adj"]["hi"] for r in rows if "adj" in r]
    if xlim is None:
        lo_d, hi_d = min(all_lo + [ref]), max(all_hi + [ref])
        pad = 0.12 * (hi_d - lo_d)
        xlim = (lo_d - pad, hi_d + pad)
    for ax in forests:
        if scale == "or":
            ax.set_xscale("log")
            ax.set_xlim(max(xlim[0], 0.2), xlim[1])
        else:
            ax.set_xlim(xlim)
        ax.axvline(ref, color=JAMA["gray"], lw=1)

    # banded group headers + rows
    for i, r in enumerate(rows):
        yy = y[i]
        if "group" in r:
            for ax in [ax_lab, ax_c, ax_ct, ax_a, ax_at]:
                ax.axhspan(yy - 0.5, yy + 0.5, color="#00000010", zorder=0)
            ax_lab.text(0.0, yy, r["group"], fontweight="bold", fontsize=8.5,
                        va="center", ha="left")
            continue
        # label + No.
        ax_lab.text(0.04, yy, r["label"], fontsize=8, va="center", ha="left")
        ax_lab.text(0.99, yy, str(r["n"]), fontsize=8, va="center", ha="right")
        # crude + adjusted markers/CI + text
        for ax, axt, key in [(ax_c, ax_ct, "crude"), (ax_a, ax_at, "adj")]:
            d = r[key]
            ax.plot([d["lo"], d["hi"]], [yy, yy], color="black", lw=1.1,
                    solid_capstyle="butt", zorder=3)
            for xc in (d["lo"], d["hi"]):
                ax.plot([xc, xc], [yy - 0.16, yy + 0.16], color="black", lw=1.1)
            ax.plot(d["est"], yy, "s", color="black", ms=5.5, zorder=4)
            axt.text(0.03, yy, _fmt(d["est"], d["lo"], d["hi"]), fontsize=7.6,
                     va="center", ha="left")

    # ---- column headers (fig-fraction, computed from axis positions) ----
    est_lab = "OR (95% CI)" if scale == "or" else "β (95% CI)"
    def cx(ax):  # center x of an axis in fig fraction
        p = ax.get_position(); return p.x0 + p.width / 2
    def lx(ax):  # left x
        return ax.get_position().x0
    fig.text(lx(ax_lab) + 0.005, hy, "Analysis", fontweight="bold", fontsize=8.5, va="bottom")
    fig.text(ax_lab.get_position().x1 - 0.005, hy, "No.", fontweight="bold",
             fontsize=8.5, va="bottom", ha="right")
    fig.text(cx(ax_c), hy, "Crude", fontweight="bold", fontsize=8.5, va="bottom", ha="center")
    fig.text(lx(ax_ct) + 0.003, hy, est_lab, fontweight="bold", fontsize=8, va="bottom")
    fig.text(cx(ax_a), hy, "Adjusted", fontweight="bold", fontsize=8.5, va="bottom", ha="center")
    fig.text(lx(ax_at) + 0.003, hy, est_lab, fontweight="bold", fontsize=8, va="bottom")

    # ---- x-axes below the forests: clean ticks, favors, single xlabel ----
    from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator
    for ax in forests:
        ax.axis("on")
        for s in ["top", "left", "right", "bottom"]:
            ax.spines[s].set_visible(False)
        ax.set_yticks([])
        if xticks is not None:
            ax.xaxis.set_major_locator(FixedLocator(xticks))
            ax.xaxis.set_major_formatter(FixedFormatter([f"{t:g}" for t in xticks]))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.tick_params(axis="x", length=3, labelsize=7, pad=2)
        # favors arrows + labels (below ticks) — only when a single polarity applies
        if favors is not None:
            ax.annotate("", xy=(0.24, -0.10), xytext=(0.44, -0.10), xycoords="axes fraction",
                        arrowprops=dict(arrowstyle="->", color=JAMA["gray"], lw=0.8))
            ax.annotate("", xy=(0.76, -0.10), xytext=(0.56, -0.10), xycoords="axes fraction",
                        arrowprops=dict(arrowstyle="->", color=JAMA["gray"], lw=0.8))
            ax.text(0.44, -0.145, favors[0], transform=ax.transAxes, fontsize=6.2,
                    ha="right", color=JAMA["gray"])
            ax.text(0.56, -0.145, favors[1], transform=ax.transAxes, fontsize=6.2,
                    ha="left", color=JAMA["gray"])
    # single centered x-axis label between the two forests
    fig.text((cx(ax_c) + cx(ax_a)) / 2, xlabel_y, xlabel, fontsize=8, ha="center")

    # heavy top/bottom rules (table style)
    for yl in (top_rule_y, bottom_frac):
        fig.add_artist(plt.Line2D([0.02, 0.985], [yl, yl], color="black",
                       lw=1.6, transform=fig.transFigure))
    if title:
        fig.text(0.02, title_y, title, fontsize=11, fontweight="bold", va="bottom")
    if covariate_note:
        fig.text(0.02, note_y, covariate_note, fontsize=6.8, color=JAMA["slate"],
                 style="italic")
    return save_all(fig, out)


def build_negcontrol_beta(seg):
    """Rows for the 1-year physical-function analysis and the leg-pain negative
    control across muscle exposures (β scale, crude|adjusted)."""
    exps = [("z_iliopsoas_voln", "Iliopsoas volume"),
            ("z_deep_back_voln", "Deep-back volume"),
            ("z_glut_med_voln", "Gluteus medius volume"),
            ("z_iliopsoas_qual", "Iliopsoas intensity"),
            ("z_deep_back_qual", "Deep-back intensity"),
            ("z_glut_med_qual", "Gluteus medius intensity")]
    rows = []
    for out, gname in [("pf", "PROMIS Physical Function, 1 y"),
                       ("leg", "Radicular leg pain, 1 y (negative control)")]:
        rows.append({"group": gname})
        for exp, elabel in exps:
            c = _beta(seg, exp, out, "1y", False)
            a = _beta(seg, exp, out, "1y", True)
            rows.append({"label": elabel, "n": a["n"], "crude": c, "adj": a})
    return rows


def render_forest_tables(seg, figdir="figures"):
    """Render both crude|adjusted JAMA forest tables from the segmented cohort."""
    jama_forest_table(
        build_primary_beta(seg), scale="beta", out=f"{figdir}/fig3_primary_forest",
        title="Preoperative cord-normalized T2 signal and postoperative recovery",
        xlabel="Adjusted β per 1 SD (95% CI)  ·  ΔODI: negative = improvement; ΔGlobal PH: positive = improvement",
        favors=None,
        xticks=[-6, -4, -2, 0, 2, 4],
        covariate_note="Crude = exposure only. Adjusted = exposure + age + sex + baseline "
        "value of the outcome (ANCOVA on change score; HC3 robust 95% CI). For ΔODI a "
        "negative β = greater improvement; for ΔGlobal Physical Health a positive β = "
        "greater improvement. n = adjusted-model complete cases.")
    jama_forest_table(
        build_mcid_or(seg), scale="or", out=f"{figdir}/fig4_mcid_forest",
        title="Muscle size vs heterogeneity and odds of achieving the MCID at 1 year",
        xlabel="Odds ratio per 1 SD (95% CI)",
        favors=("Lower odds", "Higher odds"),
        xticks=[0.5, 0.75, 1, 1.5, 2],
        covariate_note="Crude = exposure only. Adjusted = exposure + age + sex + baseline "
        "value of the outcome (logistic regression). OR<1 = lower odds of achieving the "
        "MCID. Exploratory; the ODI-MCID heterogeneity association does not replicate "
        "across instruments and does not survive multiplicity correction.")
    jama_forest_table(
        build_negcontrol_beta(seg), scale="beta", out=f"{figdir}/fig5_negcontrol_forest",
        title="Muscle exposures and 1-year physical function versus the leg-pain negative control",
        xlabel="Adjusted β per 1 SD (95% CI)  ·  ΔPROMIS-PF: positive = improvement",
        favors=None,
        xticks=[-4, -2, 0, 2, 4],
        covariate_note="Crude = exposure only. Adjusted = exposure + age + sex + baseline "
        "value of the outcome (ANCOVA on change score; HC3 robust 95% CI). No muscle "
        "exposure is associated with radicular leg-pain improvement, consistent with a "
        "decompression-governed outcome (specificity check). n = adjusted-model complete cases.")


def build_all(config_path="config.yaml"):
    from .pipeline import prepare
    _, tidy = prepare(config_path)
    seg = tidy[tidy["iliopsoas_vol"].notna()].copy()
    render_forest_tables(seg)


if __name__ == "__main__":
    build_all()
    print("wrote fig3_primary_forest and fig4_mcid_forest")
