"""JAMA Network publication figures 1-5 (WP-A4).

Every figure reads only from ``results/*.csv`` and applies the shared JAMA theme
(``src/theme.py``), so each is fully reproducible and traceable to a result cell.
Improvement convention: ΔGlobal-PH up = better, ΔODI down = better; for MCID odds,
OR<1 = lower odds of achieving the MCID.

Run:  python -m src.figures_jama   (after the pipeline has written results/)
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .theme import COL_1_5, COL_2, JAMA, apply_jama_style, save_all


def _pstar(p):
    return "*" if p < 0.05 else ""


# --------------------------------------------------------------------------- F1
def fig1_primary(results_dir="results", out="figures/fig1_primary_t2"):
    """Primary: adjusted per-SD effect of cord-normalized T2 on ΔGlobal-PH and ΔODI
    across postoperative timepoints (iliopsoas + deep back)."""
    apply_jama_style()
    t = pd.read_csv(f"{results_dir}/t2_timecourse_results.csv")
    tps = ["6w", "3m", "6m", "1y"]
    tp_lab = {"6w": "6 wk", "3m": "3 mo", "6m": "6 mo", "1y": "1 yr"}
    panels = [("ph", "Δ Global Physical Health", "higher = better", JAMA["green"]),
              ("odi", "Δ Oswestry Disability Index", "lower = better", JAMA["blue"])]
    fig, axes = plt.subplots(1, 2, figsize=(COL_2, 3.2), sharey=True)
    for ax, (outcome, title, dirn, color) in zip(axes, panels):
        sub = t[t.outcome == outcome]
        muscles = [("z_iliopsoas_rcord", "Iliopsoas", "o", color),
                   ("z_deep_back_rcord", "Deep back", "s", JAMA["orange"])]
        for exp, mlabel, mk, c in muscles:
            xs, ys, los, his = [], [], [], []
            for i, tp in enumerate(tps):
                r = sub[(sub.exposure == exp) & (sub.tp == tp)]
                if r.empty:
                    continue
                r = r.iloc[0]
                xs.append(i); ys.append(r.beta)
                los.append(r.beta - r.ci_low); his.append(r.ci_high - r.beta)
            off = -0.09 if exp.startswith("z_iliopsoas") else 0.09
            ax.errorbar(np.array(xs) + off, ys, yerr=[los, his], fmt=mk, color=c,
                        capsize=2.5, ms=5, lw=1.3, label=mlabel)
        ax.axhline(0, color=JAMA["gray"], lw=1, ls="--")
        ax.set_xticks(range(len(tps))); ax.set_xticklabels([tp_lab[t_] for t_ in tps])
        ax.set_title(title, fontsize=8.5)
        ax.text(0.02, 0.02, dirn, transform=ax.transAxes, fontsize=6.5,
                color=JAMA["gray"], style="italic")
    axes[0].set_ylabel("Adjusted β per 1 SD higher T2 (95% CI)")
    axes[0].legend(loc="upper right", fontsize=6.5)
    fig.suptitle("Cord-normalized paraspinal T2 signal and postoperative recovery",
                 fontsize=9.5, fontweight="bold", x=0.02, ha="left")
    fig.text(0.02, -0.02, "OLS on change scores, adjusted for age, sex, and baseline; "
             "HC3 robust 95% CI. Higher preoperative T2 tracks greater improvement.",
             fontsize=6, color=JAMA["gray"])
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    return save_all(fig, out)


# --------------------------------------------------------------------------- F2
def fig2_heterogeneity(results_dir="results", out="figures/fig2_heterogeneity"):
    """Heterogeneity visual summary: (A) ODI-MCID by iliopsoas texture tertile,
    (B) PROMIS-PF recovery trajectory by heterogeneity group."""
    apply_jama_style()
    tert = pd.read_csv(f"{results_dir}/tertile_mcid.csv")
    traj = pd.read_csv(f"{results_dir}/pf_trajectory.csv")
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(COL_2, 3.2))

    cats = ["Low", "Intermediate", "High"]
    odi = tert[tert.outcome == "ODI"].set_index("tertile").reindex(cats)
    yerr = [odi.pct - odi.lo, odi.hi - odi.pct]
    bar_colors = [JAMA["green"], JAMA["orange"], JAMA["red"]]
    axA.bar(cats, odi.pct, color=bar_colors, edgecolor="white", width=0.7)
    axA.errorbar(cats, odi.pct, yerr=yerr, fmt="none", ecolor=JAMA["slate"],
                 elinewidth=1, capsize=3)
    for i, (c, row) in enumerate(odi.iterrows()):
        axA.text(i, 4, f"n={int(row.n)}", ha="center", fontsize=6.5, color="white")
    axA.set_ylim(0, 100); axA.set_ylabel("Achieving ODI MCID at 1 yr (%)")
    axA.set_xlabel("Iliopsoas T2 heterogeneity (tertile)")
    axA.set_title("A  Responder gradient", loc="left", fontsize=8.5, fontweight="bold")

    # Distinct hue AND marker shape per series so the two trajectories remain
    # separable for colorblind readers and in grayscale (not color alone).
    styles = {"Low heterogeneity": (JAMA["blue"], "o"),
              "High heterogeneity": (JAMA["orange"], "s")}
    for grp, sub in traj.groupby("group"):
        sub = sub.sort_values("month")
        color, mk = styles.get(grp, (JAMA["blue"], "o"))
        axB.errorbar(sub.month, sub["mean"], yerr=1.96 * sub["sem"], marker=mk,
                     ms=4.5, capsize=2.5, color=color, lw=1.6, label=grp,
                     markerfacecolor=color, markeredgecolor="white",
                     markeredgewidth=0.5)
    axB.axhline(50, color=JAMA["gray"], ls=":", lw=1)
    axB.text(axB.get_xlim()[1], 51, "US norm", fontsize=6, color=JAMA["gray"], ha="right")
    axB.set_xlabel("Months after surgery"); axB.set_ylabel("PROMIS-PF (T-score)")
    axB.set_title("B  Functional recovery", loc="left", fontsize=8.5, fontweight="bold")
    axB.legend(fontsize=6.5, loc="lower right")
    fig.suptitle("Iliopsoas T2 heterogeneity and clinically meaningful recovery",
                 fontsize=9.5, fontweight="bold", x=0.02, ha="left")
    fig.text(0.02, -0.02, "Error bars: Wilson 95% CI (A), 95% CI of the mean (B). "
             "Exploratory; heterogeneity did not replicate across all instruments.",
             fontsize=6, color=JAMA["gray"])
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    return save_all(fig, out)


# --------------------------------------------------------------------------- F3
def fig3_size_vs_quality(results_dir="results", out="figures/fig3_size_vs_quality"):
    """Exploratory adjusted OR (per SD) of achieving MCID: muscle size (volume) vs
    quality (heterogeneity) across 3 instruments, iliopsoas."""
    apply_jama_style()
    m = pd.read_csv(f"{results_dir}/mcid_results.csv")
    m = m[m.exposure.isin(["z_iliopsoas_voln", "z_iliopsoas_texture"])]
    order = [("PROMIS-PF MCID (≥4.5)", "PROMIS-PF"),
             ("ODI MCID (≥12.8)", "ODI"),
             ("Global PH MCID (≥5)", "Global PH")]
    exp_style = {"z_iliopsoas_voln": ("Volume (size)", JAMA["gray"], "s"),
                 "z_iliopsoas_texture": ("Heterogeneity (quality)", JAMA["red"], "o")}
    fig, ax = plt.subplots(figsize=(COL_1_5, 3.0))
    yticks, ylabels = [], []
    y = 0
    for model, short in order:
        for exp, (elabel, color, mk) in exp_style.items():
            r = m[(m.model == model) & (m.exposure == exp)]
            if r.empty:
                y += 1; continue
            r = r.iloc[0]
            ax.plot([r.ci_low, r.ci_high], [y, y], color=color, lw=1.3)
            ax.plot(r["or"], y, mk, color=color, ms=6)
            ax.text(r.ci_high + 0.03, y, f"{r['or']:.2f} ({r.ci_low:.2f}–{r.ci_high:.2f})"
                    f"{_pstar(r.p)}", va="center", fontsize=6.2, color=JAMA["slate"])
            yticks.append(y); ylabels.append(f"{short} · {elabel.split()[0]}")
            y += 1
        y += 0.6
    ax.axvline(1, color=JAMA["gray"], ls="--", lw=1)
    ax.set_yticks(yticks); ax.set_yticklabels(ylabels, fontsize=6.5)
    ax.set_xlabel("Adjusted odds ratio for achieving MCID (per 1 SD)")
    ax.set_xlim(0.3, 2.2); ax.invert_yaxis()
    ax.set_title("Muscle heterogeneity, not size, tracks MCID odds",
                 fontsize=9, fontweight="bold", loc="left")
    fig.text(0.02, -0.03, "OR<1 = lower odds of achieving the MCID. * p<0.05. "
             "Only ODI-MCID reaches significance and does not replicate across instruments.",
             fontsize=5.8, color=JAMA["gray"])
    fig.tight_layout()
    return save_all(fig, out)


# --------------------------------------------------------------------------- F4
def fig4_tertile_mcid(results_dir="results", out="figures/fig4_tertile_mcid"):
    """% achieving ODI and PROMIS-PF MCID across iliopsoas heterogeneity tertiles."""
    apply_jama_style()
    tert = pd.read_csv(f"{results_dir}/tertile_mcid.csv")
    cats = ["Low", "Intermediate", "High"]
    fig, ax = plt.subplots(figsize=(COL_1_5, 3.2))
    x = np.arange(len(cats)); w = 0.38
    styles = [("ODI", JAMA["blue"], -0.5), ("PROMIS-PF", JAMA["orange"], 0.5)]
    for lab, color, off in styles:
        sub = tert[tert.outcome == lab].set_index("tertile").reindex(cats)
        yerr = [sub.pct - sub.lo, sub.hi - sub.pct]
        ax.bar(x + off * w, sub.pct, w, color=color, edgecolor="white", label=f"{lab} MCID")
        ax.errorbar(x + off * w, sub.pct, yerr=yerr, fmt="none", ecolor=JAMA["slate"],
                    elinewidth=1, capsize=2.5)
        for xi, (_, row) in zip(x + off * w, sub.iterrows()):
            ax.text(xi, 4, f"n={int(row.n)}", ha="center", fontsize=6, color="white")
    ax.set_xticks(x); ax.set_xticklabels([f"{c}" for c in cats])
    ax.set_xlabel("Iliopsoas T2 heterogeneity (tertile, low to high)")
    ax.set_ylabel("Achieving MCID at 1 year (%)"); ax.set_ylim(0, 100)
    ax.legend(fontsize=6.5, loc="upper right")
    ax.set_title("MCID attainment across heterogeneity tertiles",
                 fontsize=9, fontweight="bold", loc="left")
    fig.text(0.02, -0.03, "Error bars: Wilson 95% CI. Exploratory.", fontsize=6,
             color=JAMA["gray"])
    fig.tight_layout()
    return save_all(fig, out)


# --------------------------------------------------------------------------- F5
def fig5_pf_legpain(results_dir="results", out="figures/fig5_pf_legpain"):
    """Per-SD associations with 1-yr PROMIS-PF and the leg-pain negative control."""
    apply_jama_style()
    f = pd.read_csv(f"{results_dir}/forest_results.csv")
    exps = ["z_iliopsoas_voln", "z_deep_back_voln", "z_glut_med_voln",
            "z_iliopsoas_qual", "z_deep_back_qual", "z_glut_med_qual"]
    labels = {"z_iliopsoas_voln": "Iliopsoas volume", "z_deep_back_voln": "Deep-back volume",
              "z_glut_med_voln": "Gluteus medius volume", "z_iliopsoas_qual": "Iliopsoas intensity",
              "z_deep_back_qual": "Deep-back intensity", "z_glut_med_qual": "Gluteus medius intensity"}
    fig, ax = plt.subplots(figsize=(COL_2, 3.4))
    y = 0; yticks = []; ylabels = []
    series = [("PF 1Y (ANCOVA)", "PROMIS-PF (primary)", JAMA["blue"], -0.16),
              ("Leg pain 1Y (neg. control)", "Leg pain (neg. control)", JAMA["gray"], 0.16)]
    for exp in exps[::-1]:
        for model, slabel, color, off in series:
            r = f[(f.model == model) & (f.exposure == exp)]
            if r.empty:
                continue
            r = r.iloc[0]
            ax.plot([r.ci_low, r.ci_high], [y + off, y + off], color=color, lw=1.2)
            ax.plot(r.beta, y + off, "o", color=color, ms=4.5)
        yticks.append(y); ylabels.append(labels[exp]); y += 1
    ax.axvline(0, color=JAMA["gray"], ls="--", lw=1)
    ax.set_yticks(yticks); ax.set_yticklabels(ylabels, fontsize=7)
    ax.set_xlabel("Adjusted β per 1 SD (95% CI)")
    handles = [plt.Line2D([0], [0], color=c, marker="o", lw=1.2, label=lab)
               for _, lab, c, _ in series]
    ax.legend(handles=handles, fontsize=6.5, loc="lower right")
    ax.set_title("Muscle exposures vs 1-year physical function and the negative control",
                 fontsize=9, fontweight="bold", loc="left")
    fig.text(0.02, -0.02, "ANCOVA, age/sex/baseline-adjusted, HC3 95% CI. No exposure is "
             "associated with radicular leg pain (decompression-governed).",
             fontsize=6, color=JAMA["gray"])
    fig.tight_layout()
    return save_all(fig, out)


def build_all(results_dir="results"):
    fig1_primary(results_dir); fig2_heterogeneity(results_dir)
    fig3_size_vs_quality(results_dir); fig4_tertile_mcid(results_dir)
    fig5_pf_legpain(results_dir)


if __name__ == "__main__":
    build_all()
    print("wrote JAMA figures 1-5")
