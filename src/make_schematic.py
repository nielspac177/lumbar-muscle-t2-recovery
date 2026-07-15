"""Generate the study-design conceptual schematic (no patient data).

Exposure (preop volumetric muscle segmentation) -> lumbar decompression ->
two divergent PRO paths: SOLID "predicts" arrow to functional recovery
(PROMIS-PF / ODI), DASHED "does NOT predict" arrow to radicular leg pain
(negative control).

Output: docs/study_design_schematic.{png,svg}  (committed; conceptual, PHI-free)
Run:    python src/make_schematic.py
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import os

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

# Okabe-Ito colorblind-safe palette
BLUE = "#0072B2"
GREEN = "#009E73"
ORANGE = "#E69F00"
RED = "#D55E00"
GREY = "#444444"
LIGHT = "#F5F5F5"


def box(ax, x, y, w, h, text, fc, ec, fontsize=11, weight="normal", tc="black"):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
            linewidth=1.6, edgecolor=ec, facecolor=fc, mutation_aspect=1,
        )
    )
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, fontweight=weight, color=tc, wrap=True, zorder=5)


def arrow(ax, x0, y0, x1, y1, color, style="-", lw=2.4, label=None, lab_dy=0.12,
          label_color=None):
    ax.add_patch(
        FancyArrowPatch(
            (x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=22,
            linewidth=lw, color=color, linestyle=style,
            shrinkA=2, shrinkB=2, zorder=3,
        )
    )
    if label:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + lab_dy, label, ha="center",
                va="center", fontsize=10.5, fontweight="bold",
                color=label_color or color, zorder=6)


def main(out_base="docs/study_design_schematic"):
    fig, ax = plt.subplots(figsize=(12, 6.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.2)
    ax.axis("off")

    # ---- EXPOSURE (left) ----
    box(ax, 0.3, 4.7, 3.4, 1.1,
        "Preoperative volumetric\nmuscle segmentation\n(CT / MRI)",
        LIGHT, BLUE, fontsize=12, weight="bold", tc=BLUE)
    muscles = [("Iliopsoas", 3.55), ("Deep back (paraspinal)", 2.35),
               ("Gluteus medius", 1.15)]
    for name, yy in muscles:
        box(ax, 0.5, yy, 3.0, 0.9, f"{name}\nvolume + quality",
            "#EAF3FA", BLUE, fontsize=10)
    ax.text(2.0, 0.55, "Exposure (per 1 SD)", ha="center", fontsize=10,
            style="italic", color=GREY)

    # ---- SURGERY (center) ----
    box(ax, 4.6, 2.8, 2.4, 1.3, "Lumbar\ndecompression", "#FBEFD7", ORANGE,
        fontsize=12.5, weight="bold", tc=RED)
    arrow(ax, 3.7, 3.2, 4.6, 3.45, GREY, lw=2.0)

    # ---- OUTCOMES (right) ----
    # Functional recovery (positive, solid)
    box(ax, 8.3, 4.0, 3.4, 1.6,
        "Functional recovery\n\nPROMIS Physical Function\nODI  ·  back-pain NRS\nMCID achieved",
        "#E2F3EC", GREEN, fontsize=10.5, weight="normal", tc="black")
    # Leg pain (negative control, dashed)
    box(ax, 8.3, 1.0, 3.4, 1.4,
        "Radicular leg pain (NRS)\n\nNEGATIVE CONTROL",
        "#FBE6DD", RED, fontsize=10.5, tc="black")

    # Divergent arrows from surgery node region
    arrow(ax, 7.0, 3.7, 8.3, 4.7, GREEN, style="-", lw=2.8,
          label="PREDICTS  (H1–H3)", lab_dy=0.28)
    arrow(ax, 7.0, 3.3, 8.3, 1.7, RED, style=(0, (5, 4)), lw=2.4,
          label="does NOT predict  (H4)", lab_dy=-0.30)

    # "X" marker on the null path to emphasize dissociation
    ax.text(7.75, 2.42, "✗", ha="center", va="center", fontsize=26,
            color=RED, fontweight="bold", zorder=7)

    # Title + takeaway
    ax.text(6.0, 6.0, "Does preoperative muscle health gate functional recovery after lumbar decompression?",
            ha="center", fontsize=13, fontweight="bold", color="black")
    ax.text(6.0, 0.25,
            "Muscle volume & quality predict functional recovery (PROMIS-PF, ODI) but not radicular leg-pain relief — "
            "a dissociation that also guards against a global-frailty confound.",
            ha="center", fontsize=9.5, style="italic", color=GREY)

    os.makedirs(os.path.dirname(out_base), exist_ok=True)
    fig.tight_layout()
    fig.savefig(f"{out_base}.png", dpi=300, bbox_inches="tight")
    fig.savefig(f"{out_base}.svg", bbox_inches="tight")
    print(f"wrote {out_base}.png and {out_base}.svg")


if __name__ == "__main__":
    main()
