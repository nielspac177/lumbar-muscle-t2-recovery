"""Methods / conceptual figures for the fatproxy manuscript (WP-A3).

Three PHI-free, vector figures built with matplotlib (no external renderer):
  1. STROBE participant-flow diagram (counts from cohort.flow_counts);
  2. Causal DAG (exposure -> recovery; muscle -.-> leg-pain negative control);
  3. Segmentation & normalization workflow schematic (synthetic anatomy).

Run:  python -m src.methods_figures   (writes figures/ and docs/figures/)
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from .theme import COL_2, JAMA, apply_jama_style, save_all


def _box(ax, xy, w, h, text, fc="white", ec=None, tc=None, fontsize=8, bold=False):
    ec = ec or JAMA["slate"]
    tc = tc or JAMA["slate"]
    x, y = xy
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                 boxstyle="round,pad=0.02,rounding_size=0.02",
                 fc=fc, ec=ec, lw=1.0))
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize,
            color=tc, fontweight="bold" if bold else "normal", wrap=True)


def _arrow(ax, p0, p1, style="-", color=None, lw=1.2):
    color = color or JAMA["slate"]
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=12,
                 lw=lw, color=color, linestyle=style,
                 shrinkA=2, shrinkB=2))


# ----------------------------------------------------------------------------- 1
def strobe_flow(flow: dict, out="figures/strobe_flow"):
    """STROBE participant-flow. `flow` is cohort.flow_counts(tidy)."""
    apply_jama_style()
    fig, ax = plt.subplots(figsize=(COL_2, 6.2))
    ax.set_xlim(0, 11.4); ax.set_ylim(0, 12); ax.axis("off")
    reg = flow["registry_rows"]; seg = flow["segmented"]
    base = flow["segmented_with_baseline_PF"]; y1 = flow["segmented_with_1Y_PF"]
    steps = [
        (6, 11, f"Lumbar decompression registry\n(N = {reg:,})"),
        (6, 8.7, f"Preoperative volumetric MRI with\nL3–L5 muscle segmentation\n(n = {seg})"),
        (6, 6.4, f"Non-missing baseline\nPROMIS Physical Function\n(n = {base})"),
        (6, 4.1, f"≥ 1-year PROMIS-PF follow-up\n— primary analytic cohort —\n(n = {y1})"),
    ]
    for (x, y, t) in steps:
        primary = "primary" in t
        _box(ax, (x, y), 4.4, 1.5, t,
             fc=JAMA["green"] + "22" if primary else "white",
             ec=JAMA["green"] if primary else JAMA["slate"], bold=primary)
    for i in range(len(steps) - 1):
        _arrow(ax, (6, steps[i][1] - 0.75), (6, steps[i + 1][1] + 0.75))
    # exclusion boxes on the right
    excl = [
        (8.9, f"No preoperative MRI or\nsegmentation failed\n(n = {reg - seg:,})"),
        (6.6, f"Missing baseline PF\n(n = {seg - base})"),
        (4.3, f"No 1-year follow-up\n(n = {base - y1})"),
    ]
    for (y, t) in excl:
        _box(ax, (9.1, y), 2.6, 1.2, t, ec=JAMA["red"], tc=JAMA["red"], fontsize=6.5)
        _arrow(ax, (8.2, y + 0.35), (7.8, y + 0.35), color=JAMA["red"])
    ax.text(6, 2.7, "Instrument-specific analytic samples (segmented cohort,\n"
            "complete baseline + 1-year + covariates):", ha="center", va="center",
            fontsize=6.8, style="italic", color=JAMA["gray"])
    ax.text(6, 1.9, "ODI n = 120   ·   PROMIS-PF n = 123   ·   "
            "Global Physical Health n = 140   ·   leg-pain (neg. control) n = 133",
            ha="center", va="center", fontsize=6.8, color=JAMA["slate"])
    ax.set_title("Participant flow (STROBE)", fontsize=10, fontweight="bold", loc="left")
    return save_all(fig, out)


# ----------------------------------------------------------------------------- 2
def causal_dag(out="figures/causal_dag"):
    apply_jama_style()
    fig, ax = plt.subplots(figsize=(COL_2, 4.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    _box(ax, (2, 3), 2.6, 1.1, "Preoperative muscle\nT2 signal & heterogeneity",
         fc=JAMA["blue"] + "22", ec=JAMA["blue"], bold=True)
    _box(ax, (7.4, 4.4), 2.6, 1.0, "Functional recovery\n(PROMIS-GPH, ODI)",
         fc=JAMA["green"] + "22", ec=JAMA["green"], bold=True)
    _box(ax, (7.4, 1.4), 2.6, 1.0, "Radicular leg pain\n(negative control)",
         fc="white", ec=JAMA["gray"], tc=JAMA["gray"])
    _box(ax, (4.7, 5.3), 2.2, 0.7, "Age · Sex · Baseline PRO", fc=JAMA["orange"] + "22",
         ec=JAMA["orange"], fontsize=6.5)
    _box(ax, (4.7, 0.5), 2.0, 0.6, "Neural decompression", fc="white",
         ec=JAMA["gray"], tc=JAMA["gray"], fontsize=6.5)
    _arrow(ax, (3.3, 3.2), (6.1, 4.2), color=JAMA["green"], lw=1.6)
    _arrow(ax, (3.3, 2.8), (6.1, 1.6), style=(0, (4, 3)), color=JAMA["gray"])
    _lbl = dict(ha="center", va="center", fontsize=6.5,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))
    ax.text(4.7, 3.75, "adjusted association", color=JAMA["green"],
            rotation=17, **_lbl)
    ax.text(4.55, 2.05, "hypothesized null", color=JAMA["gray"],
            rotation=-17, **_lbl)
    # confounders -> both
    for tgt in [(6.3, 4.7), (2.0, 3.55)]:
        _arrow(ax, (4.7, 5.0), tgt, color=JAMA["orange"], lw=0.9)
    _arrow(ax, (4.9, 0.8), (6.4, 1.15), color=JAMA["gray"], lw=0.9)
    ax.set_title("Assumed causal structure", fontsize=10, fontweight="bold", loc="left")
    return save_all(fig, out)


# ----------------------------------------------------------------------------- 3
def segmentation_workflow(out="figures/methods_segmentation"):
    """Synthetic four-panel schematic of the imaging pipeline (no patient data)."""
    apply_jama_style()
    fig, axes = plt.subplots(1, 4, figsize=(COL_2, 2.4))
    rng = np.random.default_rng(7)  # figure-only; deterministic synthetic anatomy

    def axial_bg(ax):
        img = rng.normal(0.35, 0.06, (60, 60))
        ax.imshow(img, cmap="gray", vmin=0, vmax=1, extent=[0, 1, 0, 1])
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_edgecolor(JAMA["slate"]); s.set_linewidth(1)

    # ellipse helper for muscle blobs
    from matplotlib.patches import Ellipse
    # Panel A: raw T2
    axial_bg(axes[0])
    axes[0].set_title("A  Axial T2 MRI (L4)", fontsize=7.5, loc="left", fontweight="bold")

    # Panel B: segmentation overlay
    axial_bg(axes[1])
    blobs = [((0.32, 0.42), JAMA["blue"], "iliopsoas"),
             ((0.68, 0.42), JAMA["blue"], ""),
             ((0.40, 0.70), JAMA["orange"], "deep back"),
             ((0.60, 0.70), JAMA["orange"], ""),
             ((0.50, 0.55), JAMA["green"], "cord")]
    for (cx, cy), col, lab in blobs:
        r = 0.06 if col == JAMA["green"] else 0.13
        axes[1].add_patch(Ellipse((cx, cy), r * 1.4, r, fc=col, ec="white",
                          alpha=0.65, lw=0.8))
    axes[1].set_title("B  L3–L5 segmentation", fontsize=7.5, loc="left", fontweight="bold")
    axes[1].text(0.02, -0.13, "3D Slicer · TotalSegmentator", transform=axes[1].transAxes,
                 fontsize=6, color=JAMA["gray"])

    # Panel C: cord normalization
    axes[2].axis("off")
    axes[2].set_title("C  Cord normalization", fontsize=7.5, loc="left", fontweight="bold")
    axes[2].text(0.5, 0.6, r"$T2_{norm}=\dfrac{\overline{T2}_{muscle}}"
                 r"{\overline{T2}_{cord}}$", ha="center", va="center", fontsize=11,
                 color=JAMA["slate"], transform=axes[2].transAxes)
    axes[2].text(0.5, 0.25, "scanner-robust\n(internal reference)", ha="center",
                 va="center", fontsize=6.5, color=JAMA["gray"], transform=axes[2].transAxes)

    # Panel D: texture/heterogeneity
    axes[3].set_title("D  Heterogeneity (fat proxy)", fontsize=7.5, loc="left",
                      fontweight="bold")
    x = np.linspace(0, 1, 200)
    axes[3].fill_between(x, np.exp(-((x - 0.5) ** 2) / 0.02), color=JAMA["blue"],
                         alpha=0.35, label="homogeneous")
    axes[3].fill_between(x, 0.8 * np.exp(-((x - 0.4) ** 2) / 0.06)
                         + 0.6 * np.exp(-((x - 0.7) ** 2) / 0.03),
                         color=JAMA["red"], alpha=0.35, label="fatty / heterogeneous")
    axes[3].set_xticks([]); axes[3].set_yticks([])
    axes[3].set_xlabel("intramuscular T2", fontsize=6.5)
    axes[3].legend(fontsize=5.5, loc="upper right")
    for s in axes[3].spines.values():
        s.set_visible(False)
    axes[3].text(0.5, -0.18, "CV = SD/mean · spread = (p95–p5)/median",
                 transform=axes[3].transAxes, ha="center", fontsize=6, color=JAMA["gray"])

    fig.suptitle("Imaging exposure workflow", fontsize=10, fontweight="bold", x=0.02,
                 ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    return save_all(fig, out)


def _stage_label(fig, y0, y1, text):
    """Rotated stage-label box down the left margin (reference-figure style)."""
    ax = fig.add_axes([0.01, y0, 0.06, y1 - y0])
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.05, 0.05), 0.9, 0.9, boxstyle="round,pad=0.02",
                 fc="white", ec=JAMA["slate"], lw=1.1, transform=ax.transAxes))
    ax.text(0.5, 0.5, text, rotation=90, ha="center", va="center",
            fontsize=8, fontweight="bold", color=JAMA["slate"], transform=ax.transAxes)


def _synth_axial(ax, seg=False):
    rng = np.random.default_rng(7)
    ax.imshow(rng.normal(0.35, 0.06, (60, 60)), cmap="gray", vmin=0, vmax=1,
              extent=[0, 1, 0, 1])
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor(JAMA["slate"]); s.set_linewidth(1)
    if seg:
        from matplotlib.patches import Ellipse
        blobs = [((0.32, 0.42), JAMA["blue"]), ((0.68, 0.42), JAMA["blue"]),
                 ((0.40, 0.70), JAMA["orange"]), ((0.60, 0.70), JAMA["orange"]),
                 ((0.50, 0.55), JAMA["green"])]
        for (cx, cy), col in blobs:
            r = 0.06 if col == JAMA["green"] else 0.13
            ax.add_patch(Ellipse((cx, cy), r * 1.4, r, fc=col, ec="white",
                         alpha=0.7, lw=0.8))


def graphical_methods_overview(figdir="figures", out="figures/methods_overview"):
    """End-to-end staged methodology figure (reference-figure style): vertical
    stage labels down the left, each row a band of panels connected by arrows,
    from imaging through the analysis plan. This is a methods-only schematic — the
    actual result plots live in Figures 3-5 and are not duplicated here."""
    apply_jama_style()
    fig = plt.figure(figsize=(7.5, 6.9))
    bg = fig.add_axes([0, 0, 1, 1]); bg.axis("off")
    bg.set_xlim(0, 1); bg.set_ylim(0, 1)

    # The four method rows kept their original y-coordinates (0.305-0.965); with
    # the embedded-results row removed, remap that band onto the full page so the
    # rows fill the figure instead of leaving the lower third empty.
    def Y(y): return 0.055 + (y - 0.305) * (0.885 / 0.66)
    def H(h): return h * (0.885 / 0.66)

    rows = [("Imaging &\nsegmentation", 0.815, 0.965),
            ("Muscle\nexposures", 0.645, 0.795),
            ("Cohort &\noutcomes", 0.475, 0.625),
            ("Statistical\nanalysis", 0.305, 0.455)]
    for text, y0, y1 in rows:
        _stage_label(fig, Y(y0), Y(y1), text)

    def ar(p0, p1, **k):  # arrow in figure coords (y remapped)
        _arrow(bg, (p0[0], Y(p0[1])), (p1[0], Y(p1[1])), **k)

    def box(xy, w, h, text, **k):
        _box(bg, (xy[0], Y(xy[1])), w, H(h), text, **k)

    # ---- Row A: imaging & segmentation ----
    ax1 = fig.add_axes([0.11, Y(0.83), 0.13, H(0.12)]); _synth_axial(ax1)
    ax1.set_title("Preop axial T2", fontsize=6.5, color=JAMA["slate"])
    ax2 = fig.add_axes([0.34, Y(0.83), 0.13, H(0.12)]); _synth_axial(ax2, seg=True)
    ax2.set_title("L3–L5 segmentation", fontsize=6.5, color=JAMA["slate"])
    box((0.66, 0.89), 0.20, 0.085,
        "Iliopsoas · deep back ·\ngluteus medius · cord ·\nvertebra (3D Slicer /\nTotalSegmentator v5.8.1)",
        fontsize=6.3)
    ar((0.245, 0.89), (0.335, 0.89)); ar((0.475, 0.89), (0.555, 0.89))

    # ---- Row B: exposures ----
    box((0.20, 0.72), 0.20, 0.09,
        "Cord normalization\n" + r"$T2_{norm}=\overline{T2}_{musc}/\overline{T2}_{cord}$",
        fontsize=7, fc=JAMA["blue"] + "18", ec=JAMA["blue"])
    axh = fig.add_axes([0.40, Y(0.655), 0.16, H(0.10)])
    x = np.linspace(0, 1, 200)
    axh.fill_between(x, np.exp(-((x - 0.5) ** 2) / 0.02), color=JAMA["blue"], alpha=0.35)
    axh.fill_between(x, 0.8 * np.exp(-((x - 0.4) ** 2) / 0.06) + 0.6 * np.exp(-((x - 0.7) ** 2) / 0.03),
                     color=JAMA["red"], alpha=0.35)
    axh.set_xticks([]); axh.set_yticks([])
    for s in axh.spines.values(): s.set_visible(False)
    axh.set_title("Heterogeneity (CV, spread)", fontsize=6.3, color=JAMA["slate"])
    box((0.79, 0.72), 0.18, 0.085,
        "z-scored, per-SD:\nsignal · heterogeneity\n· volume", fontsize=6.6,
        fc=JAMA["green"] + "18", ec=JAMA["green"])
    ar((0.30, 0.72), (0.40, 0.72)); ar((0.56, 0.72), (0.70, 0.72))

    # ---- Row C: cohort & outcomes ----
    box((0.17, 0.55), 0.15, 0.07, "Registry\nN = 2344", fontsize=6.6)
    box((0.37, 0.55), 0.15, 0.07, "Segmented\nn = 385", fontsize=6.6)
    box((0.57, 0.55), 0.16, 0.07, "Analyzed\nn = 118–140", fontsize=6.6,
        fc=JAMA["green"] + "18", ec=JAMA["green"])
    ar((0.245, 0.55), (0.295, 0.55)); ar((0.445, 0.55), (0.49, 0.55))
    box((0.83, 0.55), 0.17, 0.085,
        "PROMIS-PF 33.7 to 41.6\nODI 48.6 to 27.4\n(1-year)", fontsize=6.4)
    ar((0.65, 0.55), (0.745, 0.55))

    # ---- Row D: analysis ----
    dboxes = [("Adjusted Δ models\n(age, sex, baseline;\nHC3 robust SE)", 0.175),
              ("MCID logistic\n(odds ratio, per SD)", 0.395),
              ("Leg-pain\nnegative control", 0.615),
              ("Multiplicity (Holm/\nFDR) + fragility", 0.835)]
    for txt, cx in dboxes:
        box((cx, 0.38), 0.165, 0.085, txt, fontsize=6.4,
            fc=JAMA["orange"] + "15", ec=JAMA["orange"])
    for cx in (0.175, 0.395, 0.615):
        ar((cx + 0.083, 0.38), (cx + 0.137, 0.38))

    bg.text(0.01, 0.985, "Study methodology overview", fontsize=11, fontweight="bold",
            color=JAMA["slate"], va="top")
    return save_all(fig, out)


def build_all(config_path="config.yaml"):
    from .cohort import flow_counts
    from .pipeline import prepare
    _, tidy = prepare(config_path)
    strobe_flow(flow_counts(tidy))
    causal_dag()
    segmentation_workflow()
    graphical_methods_overview()


if __name__ == "__main__":
    build_all()
    print("wrote methods figures: strobe_flow, causal_dag, methods_segmentation")
