"""End-to-end analysis orchestration (PLAN.md §5, §6).

    config -> load -> tidy -> cohort -> models -> figures
"""
from __future__ import annotations

import os

import pandas as pd

from .analysis import (
    mcid_table,
    ph_mcid_threshold_sweep,
    quality_direction,
    run_all,
    t2_timecourse_table,
)
from .cleaning import make_tidy
from .cohort import completer_comparison, completers_vs_noncompleters, flow_counts
from .data_loading import load_config, load_raw
from .figure_data import build_figure_data
from .figures import (
    graphical_abstract,
    jama_forest,
    jama_forest_or,
    mcid_by_tertile,
    trajectory_plot,
)
from .figures_jama import build_all as build_jama_figures
from .forest_tables import render_forest_tables
from .methods_figures import (
    causal_dag,
    graphical_methods_overview,
    segmentation_workflow,
    strobe_flow,
)
from .robustness import (
    build_robustness_table,
    fragility_index,
    ipw_headline,
    reference_sensitivity,
)


def prepare(config_path: str = "config.yaml"):
    """Load the workbook and build the tidy, analysis-ready per-patient frame."""
    cfg = load_config(config_path)
    data = load_raw(cfg)
    tidy = make_tidy(data, cfg)
    return cfg, tidy


def run(config_path: str = "config.yaml", outdir="results", figdir="figures"):
    """Run the full study pipeline and write result tables and figures."""
    os.makedirs(outdir, exist_ok=True)
    cfg, tidy = prepare(config_path)

    flow = flow_counts(tidy)
    # Segmented cohort; each model drops to its own outcome's complete cases so that
    # ODI and PROMIS-PF analyses each use their maximal available sample.
    seg = tidy[tidy["iliopsoas_vol"].notna()].copy()

    qdir = quality_direction(seg)
    t2tc = t2_timecourse_table(seg)        # PRIMARY: cord-normalized T2 -> recovery over time
    results = run_all(seg)                 # continuous ANCOVA (PF + leg-pain control)
    mcid = mcid_table(seg)                 # SECONDARY: size vs quality -> MCID odds
    ph_sweep = ph_mcid_threshold_sweep(seg)  # sensitivity: Global-PH MCID threshold
    robustness = build_robustness_table(seg)  # multiplicity + headline sensitivity

    figdata = build_figure_data(seg)       # tertile MCID rates + PF trajectory (for figs)
    frag = fragility_index(seg)            # headline ODI-MCID fragility index
    ipw = ipw_headline(seg)                # attrition-weighted headline sensitivity
    refsens = reference_sensitivity(seg)   # primary result vs choice of internal reference

    robustness.to_csv(f"{outdir}/robustness_table.csv", index=False)
    ph_sweep.to_csv(f"{outdir}/ph_mcid_threshold_sweep.csv", index=False)
    t2tc.to_csv(f"{outdir}/t2_timecourse_results.csv", index=False)
    results.to_csv(f"{outdir}/forest_results.csv", index=False)
    mcid.to_csv(f"{outdir}/mcid_results.csv", index=False)
    qdir.to_csv(f"{outdir}/quality_direction.csv", index=False)
    completers_vs_noncompleters(tidy).to_csv(f"{outdir}/attrition.csv")
    # Attrition stratified by the ODI outcome that carries the exploratory finding
    completer_comparison(tidy, "odi").to_csv(f"{outdir}/attrition_odi.csv", index=False)
    completer_comparison(tidy, "pf").to_csv(f"{outdir}/attrition_pf.csv", index=False)
    figdata["tertile_mcid"].to_csv(f"{outdir}/tertile_mcid.csv", index=False)
    figdata["pf_trajectory"].to_csv(f"{outdir}/pf_trajectory.csv", index=False)
    pd.DataFrame([frag]).to_csv(f"{outdir}/fragility.csv", index=False)
    ipw.to_csv(f"{outdir}/ipw_headline.csv", index=False)
    refsens.to_csv(f"{outdir}/reference_sensitivity.csv", index=False)

    # PRIMARY figure: cord-normalized T2 signal vs change in PH and ODI over time
    jama_forest(t2tc, out=f"{figdir}/forest_t2_timecourse.png",
                title="Cord-normalized paraspinal T2 signal and postoperative recovery",
                xlabel="← worse change      |      better change →   (ΔPH ↑ better; ΔODI ↓ better)",
                col_header="Muscle (per 1 SD higher T2)")
    jama_forest_or(mcid, out=f"{figdir}/forest_mcid.png")          # secondary
    jama_forest(results, out=f"{figdir}/forest_pf_legpain.png")    # neg control
    mcid_by_tertile(tidy, out=f"{figdir}/mcid_by_tertile.png")
    graphical_abstract(tidy, out=f"{figdir}/graphical_abstract.png")
    trajectory_plot(tidy, out=f"{figdir}/trajectory.png", strat="z_iliopsoas_texture")

    # JAMA publication figures 1-5 (read from the results/*.csv just written)
    build_jama_figures(results_dir=outdir)
    # Crude|adjusted JAMA forest tables (primary β and exploratory MCID OR)
    render_forest_tables(seg, figdir=figdir)
    # Methods / conceptual figures (STROBE flow, causal DAG, segmentation schematic)
    strobe_flow(flow, out=f"{figdir}/strobe_flow")
    causal_dag(out=f"{figdir}/causal_dag")
    segmentation_workflow(out=f"{figdir}/methods_segmentation")
    # Staged methodology overview (embeds the result figures just written)
    graphical_methods_overview(figdir=figdir, out=f"{figdir}/methods_overview")

    return {"flow": flow, "t2_timecourse": t2tc, "results": results,
            "mcid": mcid, "quality_direction": qdir, "fragility": frag}


if __name__ == "__main__":
    run()
