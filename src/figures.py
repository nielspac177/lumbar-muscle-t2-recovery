"""Figures for the abstract (PLAN.md §9). Saved to figures/ (gitignored).

The forest figure follows the JAMA convention: a table whose rows carry the
point estimate, 95% CI, and p-value as text columns, with an aligned forest
panel (markers, CI whiskers, and a null reference line) on the right.
"""
from __future__ import annotations

import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import gridspec

LABELS = {
    "z_iliopsoas_voln": "Iliopsoas, volume index",
    "z_deep_back_voln": "Deep back, volume index",
    "z_glut_med_voln": "Gluteus medius, volume index",
    "z_composite_voln": "Composite volume index",
    "z_iliopsoas_qual": "Iliopsoas, mean intensity",
    "z_deep_back_qual": "Deep back, mean intensity",
    "z_glut_med_qual": "Gluteus medius, mean intensity",
    "z_iliopsoas_texture": "Iliopsoas, fatty infiltration",
    "z_deep_back_texture": "Deep back, fatty infiltration",
    "z_glut_med_texture": "Gluteus medius, fatty infiltration",
}
BLUE, GREY = "#0072B2", "#555555"


def jama_forest_or(results: pd.DataFrame, out="figures/forest_mcid.png"):
    """JAMA-style table + forest for odds ratios (log scale, null reference at 1).

    `results` columns: model, exposure, or, ci_low, ci_high, p, n.
    """
    groups = list(dict.fromkeys(results["model"]))
    rows = []
    for gm in groups:
        rows.append(("group", gm))
        for _, r in results[results["model"] == gm].iterrows():
            rows.append(("row", r))
    n = len(rows)
    ypos = {i: n - i for i in range(n)}
    lo = min(results["ci_low"].min(), 0.45)
    hi = max(results["ci_high"].max(), 2.0)

    fig = plt.figure(figsize=(13, 0.52 * n + 1.3))
    gs = gridspec.GridSpec(1, 2, width_ratios=[2.0, 1.0], wspace=0.02)
    axt = fig.add_subplot(gs[0]); axp = fig.add_subplot(gs[1])
    for ax in (axt, axp):
        ax.set_ylim(0.3, n + 1.2)
    axt.axis("off"); axt.set_xlim(0, 1.4)
    X_LABEL, X_OR, X_P = 0.00, 0.70, 1.16
    axt.text(X_LABEL, n + 0.9, "Muscle exposure (per 1 SD)", fontsize=10.5, fontweight="bold")
    axt.text(X_OR, n + 0.9, "OR (95% CI)", fontsize=10.5, fontweight="bold")
    axt.text(X_P, n + 0.9, "P value", fontsize=10.5, fontweight="bold")

    axp.set_xscale("log")
    axp.set_xlim(lo * 0.9, hi * 1.1)
    axp.axvline(1, color=GREY, lw=1.1, ls="--", zorder=1)
    for s in ("top", "right", "left"):
        axp.spines[s].set_visible(False)
    axp.set_yticks([])
    import matplotlib.ticker as mticker
    axp.set_xticks([0.5, 0.7, 1.0, 1.5, 2.0])
    axp.xaxis.set_major_formatter(mticker.ScalarFormatter())
    axp.xaxis.set_minor_locator(mticker.NullLocator())
    axp.xaxis.set_minor_formatter(mticker.NullFormatter())
    axp.tick_params(axis="x", labelsize=8.5)
    axp.set_xlabel("← lower odds of MCID      |      higher odds of MCID →", fontsize=8, color=GREY)

    for i, (kind, payload) in enumerate(rows):
        y = ypos[i]
        if kind == "group":
            axt.text(-0.02, y, payload, fontsize=10, fontweight="bold", style="italic")
            continue
        r = payload
        sig = r["p"] < 0.05
        axt.text(0.03, y, LABELS.get(r["exposure"], r["exposure"]), fontsize=9.3)
        axt.text(X_OR, y, f"{r['or']:.2f} ({r['ci_low']:.2f}–{r['ci_high']:.2f})",
                 fontsize=9.0, fontweight="bold" if sig else "normal")
        axt.text(X_P, y, _fmt_p(r["p"]), fontsize=9.0, fontweight="bold" if sig else "normal")
        axp.plot([r["ci_low"], r["ci_high"]], [y, y], color=BLUE, lw=1.6, zorder=2)
        axp.scatter([r["or"]], [y], s=46, color=BLUE, edgecolor="white", linewidth=0.8, zorder=3)

    fig.suptitle("Muscle size vs quality and odds of achieving MCID at 1 year",
                 fontsize=12.5, fontweight="bold", y=0.99)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=300, bbox_inches="tight")
    fig.savefig(out.replace(".png", ".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def _fmt_p(p):
    return "<.001" if p < 0.001 else f"{p:.3f}".lstrip("0")


def jama_forest(results: pd.DataFrame, out="figures/forest_pf_legpain.png",
                title="Muscle morphology and 1-year outcomes after lumbar decompression",
                xlabel="Worse ←   favours lower muscle      |      favours higher muscle   → better",
                col_header="Muscle exposure (per 1 SD)"):
    """Render a JAMA-style table + forest figure grouped by model.

    `results` columns: model, exposure, beta, ci_low, ci_high, p, n (optional: label).
    """
    groups = list(dict.fromkeys(results["model"]))      # preserve order
    # Build the row layout: a header line per group, then its exposures.
    rows = []  # (kind, payload)
    for gmodel in groups:
        rows.append(("group", gmodel))
        sub = results[results["model"] == gmodel]
        for _, r in sub.iterrows():
            rows.append(("row", r))
    n = len(rows)
    ypos = {i: n - i for i in range(n)}                 # top to bottom

    lo = min(results["ci_low"].min(), -0.1)
    hi = max(results["ci_high"].max(), 0.1)
    pad = 0.15 * (hi - lo)

    fig = plt.figure(figsize=(12.5, 0.52 * n + 1.2))
    gs = gridspec.GridSpec(1, 2, width_ratios=[1.55, 1.0], wspace=0.02)
    axt = fig.add_subplot(gs[0]); axp = fig.add_subplot(gs[1])
    for ax in (axt, axp):
        ax.set_ylim(0.3, n + 1.2); ax.axis("off")

    X_LABEL, X_CI, X_P = 0.00, 0.56, 1.06
    # Column headers
    axt.text(X_LABEL, n + 0.9, col_header, fontsize=10.5, fontweight="bold")
    axt.text(X_CI, n + 0.9, "β (95% CI)", fontsize=10.5, fontweight="bold", ha="left")
    axt.text(X_P, n + 0.9, "P value", fontsize=10.5, fontweight="bold", ha="left")

    axt.set_xlim(0, 1.3)
    axp.set_xlim(lo - pad, hi + pad)
    axp.axvline(0, color=GREY, lw=1.1, ls="--", zorder=1)

    for i, (kind, payload) in enumerate(rows):
        y = ypos[i]
        if kind == "group":
            axt.text(-0.02, y, payload, fontsize=10, fontweight="bold", style="italic")
            continue
        r = payload
        label = r["label"] if "label" in r and pd.notna(r.get("label")) else LABELS.get(r["exposure"], r["exposure"])
        sig = r["p"] < 0.05
        axt.text(0.03, y, label, fontsize=9.5)
        axt.text(X_CI, y, f"{r['beta']:.2f} ({r['ci_low']:.2f} to {r['ci_high']:.2f})",
                 fontsize=9.0, ha="left", fontweight="bold" if sig else "normal")
        axt.text(X_P, y, _fmt_p(r["p"]), fontsize=9.0, ha="left",
                 fontweight="bold" if sig else "normal")
        axp.plot([r["ci_low"], r["ci_high"]], [y, y], color=BLUE, lw=1.6, zorder=2)
        axp.scatter([r["beta"]], [y], s=46, color=BLUE,
                    edgecolor="white", linewidth=0.8, zorder=3)

    # x-axis ticks for the forest panel only
    axp.axis("on")
    for s in ("top", "right", "left"):
        axp.spines[s].set_visible(False)
    axp.set_yticks([])
    axp.tick_params(axis="x", labelsize=8.5)
    axp.set_xlabel(xlabel, fontsize=8, color=GREY)

    fig.suptitle(title, fontsize=12.5, fontweight="bold", y=0.99)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=300, bbox_inches="tight")
    fig.savefig(out.replace(".png", ".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


# Okabe-Ito colourblind-safe palette
OI_BLUE, OI_ORANGE, OI_GREEN, OI_VERM = "#0072B2", "#E69F00", "#009E73", "#D55E00"


def _wilson(k, n):
    """Wilson 95% CI for a proportion (no SciPy dependency)."""
    if n == 0:
        return (np.nan, np.nan, np.nan)
    z = 1.959963985
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return p, max(0, centre - half), min(1, centre + half)


def mcid_by_tertile(tidy: pd.DataFrame, out="figures/mcid_by_tertile.png",
                    strat="z_iliopsoas_texture"):
    """Grouped bars: % achieving MCID (ODI and PROMIS-PF) across iliopsoas
    fatty-infiltration tertiles, with Wilson 95% CIs and per-bar n."""
    d = tidy[tidy[strat].notna()].copy()
    d["tertile"] = pd.qcut(d[strat], 3, labels=["Low", "Intermediate", "High"])
    outcomes = [("ODI", "odi_mcid_1y", OI_BLUE), ("PROMIS-PF", "pf_mcid_1y", OI_ORANGE)]
    cats = ["Low", "Intermediate", "High"]
    x = np.arange(len(cats)); w = 0.38

    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for j, (lab, flag, color) in enumerate(outcomes):
        ps, los, his, ns = [], [], [], []
        for c in cats:
            s = d.loc[d["tertile"] == c, flag].dropna()
            p, lo, hi = _wilson(int(s.sum()), len(s))
            ps.append(100 * p); los.append(100 * (p - lo)); his.append(100 * (hi - p)); ns.append(len(s))
        ax.bar(x + (j - 0.5) * w, ps, w, color=color, label=f"{lab} MCID", edgecolor="white")
        ax.errorbar(x + (j - 0.5) * w, ps, yerr=[los, his], fmt="none",
                    ecolor="#333", elinewidth=1.1, capsize=3)
        for xi, p, nn in zip(x + (j - 0.5) * w, ps, ns):
            ax.text(xi, 3, f"n={nn}", ha="center", va="bottom", fontsize=7.5, color="white")

    ax.set_xticks(x); ax.set_xticklabels([f"{c}\nfatty infiltration" for c in cats])
    ax.set_ylabel("Patients achieving MCID at 1 year (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Clinically meaningful recovery declines with iliopsoas fatty infiltration",
                 fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.text(0.0, -0.16, "Tertiles of preoperative iliopsoas textural heterogeneity (low → high fatty infiltration). "
            "Error bars: Wilson 95% CI.", transform=ax.transAxes, fontsize=7.5, color=GREY)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=300, bbox_inches="tight")
    fig.savefig(out.replace(".png", ".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def graphical_abstract(tidy: pd.DataFrame, out="figures/graphical_abstract.png"):
    """Two-panel visual summary: responder gradient (A) and recovery trajectory (B)."""
    months = {"base": 0, "6w": 1.5, "3m": 3, "6m": 6, "1y": 12, "2y": 24}
    d = tidy[tidy["z_iliopsoas_texture"].notna()].copy()
    d["tertile"] = pd.qcut(d["z_iliopsoas_texture"], 3, labels=["Low", "Intermediate", "High"])
    d["half"] = np.where(d["z_iliopsoas_texture"] >= d["z_iliopsoas_texture"].median(),
                         "High fatty infiltration", "Low fatty infiltration")

    fig = plt.figure(figsize=(11, 4.4))
    gs = fig.add_gridspec(1, 2, wspace=0.28)
    axA, axB = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])

    # Panel A: ODI MCID rate across tertiles
    cats = ["Low", "Intermediate", "High"]
    ps, los, his, ns = [], [], [], []
    for c in cats:
        s = d.loc[d["tertile"] == c, "odi_mcid_1y"].dropna()
        p, lo, hi = _wilson(int(s.sum()), len(s))
        ps.append(100 * p); los.append(100 * (p - lo)); his.append(100 * (hi - p)); ns.append(len(s))
    colors = [OI_GREEN, OI_ORANGE, OI_VERM]
    axA.bar(cats, ps, color=colors, edgecolor="white")
    axA.errorbar(cats, ps, yerr=[los, his], fmt="none", ecolor="#333", elinewidth=1.1, capsize=3)
    for xi, p, nn in zip(cats, ps, ns):
        axA.text(xi, 3, f"n={nn}", ha="center", fontsize=8, color="white")
    axA.set_ylabel("Achieving ODI MCID at 1 year (%)"); axA.set_ylim(0, 100)
    axA.set_xlabel("Iliopsoas fatty infiltration (tertile)")
    axA.set_title("A  Responder gradient", fontweight="bold", loc="left", fontsize=11)
    for s in ("top", "right"):
        axA.spines[s].set_visible(False)

    # Panel B: PROMIS-PF trajectory by low vs high FI
    for g, color in [("Low fatty infiltration", OI_GREEN), ("High fatty infiltration", OI_VERM)]:
        sub = d[d["half"] == g]; xs, ys, es = [], [], []
        for t, mo in months.items():
            v = sub[f"pf_{t}"].dropna()
            if len(v) >= 5:
                xs.append(mo); ys.append(v.mean()); es.append(1.96 * v.sem())
        axB.errorbar(xs, ys, yerr=es, marker="o", capsize=3, color=color, lw=2, label=g)
    axB.axhline(50, color=GREY, ls=":", lw=1)
    axB.text(24, 50.4, "US norm", fontsize=7.5, color=GREY, ha="right")
    axB.set_xlabel("Months after surgery"); axB.set_ylabel("PROMIS Physical Function (T-score)")
    axB.set_title("B  Functional recovery", fontweight="bold", loc="left", fontsize=11)
    axB.legend(frameon=False, fontsize=8.5, loc="lower right")
    for s in ("top", "right"):
        axB.spines[s].set_visible(False)

    fig.suptitle("Iliopsoas muscle quality, not quantity, tracks recovery after lumbar decompression",
                 fontsize=12.5, fontweight="bold", y=1.02)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=300, bbox_inches="tight")
    fig.savefig(out.replace(".png", ".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def trajectory_plot(tidy: pd.DataFrame, out="figures/trajectory.png",
                    strat="z_iliopsoas_voln"):
    """PROMIS-PF over time, stratified by low vs high muscle (median split)."""
    months = {"base": 0, "6w": 1.5, "3m": 3, "6m": 6, "1y": 12, "2y": 24}
    seg = tidy[tidy[strat].notna()].copy()
    # For a texture/fatty-infiltration metric, higher = worse muscle quality.
    if "texture" in strat or "_cv" in strat or "spread" in strat:
        hi_lab, lo_lab = "High fatty infiltration", "Low fatty infiltration"
        good = lo_lab
    else:
        hi_lab, lo_lab = "Higher muscle", "Lower muscle"
        good = hi_lab
    seg["grp"] = np.where(seg[strat] >= seg[strat].median(), hi_lab, lo_lab)
    fig, ax = plt.subplots(figsize=(7.5, 5))
    colors = {good: "#009E73", (lo_lab if good == hi_lab else hi_lab): "#D55E00"}
    for g, sub in seg.groupby("grp"):
        xs, ys, es = [], [], []
        for t, mo in months.items():
            v = sub[f"pf_{t}"].dropna()
            if len(v) >= 5:
                xs.append(mo); ys.append(v.mean()); es.append(1.96 * v.sem())
        ax.errorbar(xs, ys, yerr=es, marker="o", capsize=3, color=colors[g],
                    label=f"{g} (n≈{int(sub['pf_base'].notna().sum())})", lw=2)
    ax.axhline(50, color=GREY, ls=":", lw=1, label="US population norm")
    ax.set_xlabel("Months after surgery"); ax.set_ylabel("PROMIS Physical Function (T-score)")
    ax.set_title("Physical-function recovery by preoperative muscle status", fontweight="bold")
    ax.legend(frameon=False, fontsize=9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=300, bbox_inches="tight")
    fig.savefig(out.replace(".png", ".svg"), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")
