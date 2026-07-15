# lumbar-muscle-pro

Reproducible analysis code for an observational study of **preoperative paraspinal
and iliopsoas muscle MRI T2 signal and functional recovery after lumbar
decompression** (retrospective single-center cohort, N = 385).

This repository is **code and analysis documentation only** — no manuscript and no
patient data. Its purpose is to let others read the exact analysis, inspect the
modeling choices, and reproduce every reported statistic. The one figure included is
the methods schematic below (a PHI-free overview of the pipeline).

## Analysis overview

![Study methodology overview: preoperative axial T2 MRI and L3–L5 segmentation; cord-normalized T2 signal and heterogeneity index; cohort derivation and 1-year outcome change; adjusted change models with HC3 robust SE, MCID logistic regression, the leg-pain negative control, and multiplicity/fragility assessment.](docs/img/methods_overview.png)

*Preoperative axial T2 MRI and L3–L5 segmentation → cord-normalized T2 signal and a
heterogeneity (texture) index → cohort derivation and 1-year outcome change →
adjusted change models (HC3 robust SE), MCID logistic regression, a leg-pain negative
control, and multiplicity/fragility assessment. Anatomical panels are schematic and
contain no patient data.*

## What the analysis does

Muscle T2 signal of the iliopsoas and deep back muscles is normalized to a same-image
central-canal reference (making it robust to scanner and sequence), modeled with
adjustment for age, sex, and baseline outcome using HC3 robust standard errors, and
tested for specificity against a prespecified radicular leg-pain negative control.
Change in PROMIS Global Physical Health and the Oswestry Disability Index through one
year are the outcomes; attainment of each instrument's minimal clinically important
difference (MCID) is modeled by logistic regression. Multiplicity (Holm, Benjamini–
Hochberg), fragility, and inverse-probability-of-attrition weighting are reported as
sensitivity analyses.

The analysis is fully deterministic (no random number generation).

## Reproducing the results

```bash
make setup                              # .venv + pinned dependencies
cp config.example.yaml config.yaml      # then set DATA_PATH to the local workbook
make repro                              # == python -m src.pipeline
make verify                             # runs twice, asserts results/ are identical
```

Patient data are **not** included (see below), so `make repro` requires access to the
source workbook. To let anyone check the numbers without the data, the **aggregate
result tables** (model estimates only, no row-level data) are committed under
[`results/`](results); every reported statistic is traced to a `results/*.csv` cell in
[`docs/NUMBERS_LEDGER.md`](docs/NUMBERS_LEDGER.md).

## Tests (no data required)

```bash
make test        # pytest on tiny hand-mocked frames — no patient data used
make lint        # ruff
```

Continuous integration runs lint + tests on every push (`.github/workflows/ci.yml`).

## Repository layout

| Path | Contents |
| --- | --- |
| `src/data_loading.py` | Read the workbook and flatten its two-row header |
| `src/cleaning.py` | Derive analysis variables; handle outliers and units |
| `src/cohort.py` | Assemble the analytic cohort and attrition/flow counts |
| `src/analysis.py` | ANCOVA change models, MCID logistic, negative control |
| `src/robustness.py` | Multiplicity, fragility, IPW sensitivity |
| `src/pipeline.py` | End-to-end orchestration (`python -m src.pipeline`) |
| `results/*.csv` | Committed aggregate estimates (PHI-free) |
| `docs/CODE_WALKTHROUGH.md` | Line-by-line explanation of the analysis code |
| `docs/NUMBERS_LEDGER.md` | Every statistic → exact function + `results/` cell |
| `docs/STATS_VERIFICATION.md` | Independent re-derivation of contested numbers |
| `docs/DISCREPANCY_LOG.md` | Number-changing bug fixes and their effect |
| `docs/adr/` | Architecture decision records (normalization, texture, HC3, etc.) |
| `docs/ENVIRONMENT.md` | Python / OS / dependency provenance |
| `PLAN.md` | Original pre-analysis plan (provenance) |

The `src/` modules that render figures are part of the reproducible pipeline; running
`make repro` writes them to a local `figures/` directory, which is git-ignored.

## Data availability and ethics

The source dataset comprises imaging-derived muscle segmentations linked to
longitudinal patient-reported outcomes and contains protected health information.
**No patient data are stored in this repository.** Analyses read the workbook from a
local path defined in `config.yaml` (git-ignored); `.gitignore` additionally blocks
all tabular, spreadsheet, and imaging file formats as a second safeguard.
Investigators with appropriate approvals should obtain the dataset through the study's
data-governance process. See [`DATA_AVAILABILITY.md`](DATA_AVAILABILITY.md).

## Citation and license

See [`CITATION.cff`](CITATION.cff) and [`LICENSE`](LICENSE).
