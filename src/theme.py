"""Shared JAMA Network figure theme (Appendix S1 of the study plan).

Canonical ggsci ``pal_jama`` palette plus matplotlib rcParams so every figure in
this repo renders with one consistent, colorblind-aware, print-ready style. Import
``apply_jama_style()`` at the top of any figure module and use the ``JAMA`` colors.
"""
from __future__ import annotations

import matplotlib as mpl

# Canonical JAMA palette (ggsci pal_jama)
JAMA = {
    "slate": "#374E55",   # text / axes / primary dark
    "orange": "#DF8F44",  # secondary / contrast
    "blue": "#00A1D5",    # primary data series
    "red": "#B24745",     # emphasis / harm
    "green": "#79AF97",   # benefit / improvement
    "purple": "#6A6599",  # tertiary
    "gray": "#80796B",    # reference / null
}
JAMA_CYCLE = [JAMA["blue"], JAMA["orange"], JAMA["green"], JAMA["red"],
              JAMA["purple"], JAMA["slate"], JAMA["gray"]]

# JAMA single/1.5/double column widths in inches (design at final size)
COL_1 = 3.35
COL_1_5 = 5.0
COL_2 = 7.0


def apply_jama_style():
    """Set global rcParams to the JAMA house style. Idempotent."""
    mpl.rcParams.update({
        "figure.dpi": 150,
        "savefig.dpi": 600,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "axes.edgecolor": JAMA["slate"],
        "axes.labelcolor": JAMA["slate"],
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.prop_cycle": mpl.cycler(color=JAMA_CYCLE),
        "xtick.color": JAMA["slate"],
        "ytick.color": JAMA["slate"],
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "legend.frameon": False,
        "text.color": JAMA["slate"],
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.bbox": "tight",
        # Keep SVG text as editable <text> elements (not outlined paths) so the
        # exported panels can be relabelled/restyled in Illustrator/Inkscape/Figma.
        "svg.fonttype": "none",
    })


def save_all(fig, stem: str):
    """Save a figure as vector (SVG, PDF) + 600-dpi PNG under a common stem.

    ``stem`` is a path without extension, e.g. ``figures/fig1_primary``.
    """
    import os
    os.makedirs(os.path.dirname(stem) or ".", exist_ok=True)
    for ext in ("svg", "pdf", "png"):
        fig.savefig(f"{stem}.{ext}")
    return stem
