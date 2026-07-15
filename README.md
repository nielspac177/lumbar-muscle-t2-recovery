# Reproducible analysis: preoperative paraspinal and iliopsoas muscle T2 signal and functional recovery after lumbar decompression

Analysis code and computational provenance for a retrospective, single-center cohort
study (N = 385). This repository accompanies the manuscript and exists to make the
analysis transparent and independently reproducible. It provides the analysis
pipeline, the unit tests, the pinned software environment, the aggregate result
tables, and the decision records that document each methodological choice.

The repository holds **no patient data and no manuscript**. The only figure is the
methods schematic below, which contains no patient data.

## Study summary

- **Design.** Retrospective observational cohort, reported per the STROBE guideline.
- **Setting and participants.** A single academic medical center, 2016–2024; 385
  adults who underwent lumbar decompression and had a preoperative volumetric MRI
  amenable to L3–L5 muscle segmentation.
- **Exposures.** Cord-normalized mean T2 signal (muscle intensity divided by a
  same-image central-canal reference) and an intramuscular T2 heterogeneity (texture)
  index for the iliopsoas and deep back muscles, standardized within the cohort.
- **Outcomes.** Change in the Oswestry Disability Index and PROMIS Global Physical
  Health through one year, and attainment of each instrument's minimal clinically
  important difference (MCID).
- **Statistical analysis.** Covariate-adjusted change-score models (age, sex, and
  baseline value) with HC3 heteroskedasticity-consistent standard errors; MCID
  logistic regression; a prespecified radicular leg-pain negative control; and
  Holm and Benjamini–Hochberg multiplicity correction, a fragility-index analysis,
  and inverse-probability-of-attrition weighting as sensitivity analyses.

The cord-normalized T2 analysis was developed after a prespecified (and null) muscle-
volume analysis. It is therefore post-hoc, and the findings are hypothesis-generating;
the source code and the architecture decision records (`docs/adr/`) state this
explicitly.

## Analysis overview

![Study methodology overview: preoperative axial T2 MRI and L3–L5 segmentation; cord-normalized T2 signal and heterogeneity index; cohort derivation and 1-year outcome change; adjusted change models with HC3 robust standard errors, MCID logistic regression, a leg-pain negative control, and multiplicity and fragility assessment.](docs/img/methods_overview.png)

*Preoperative axial T2 MRI and L3–L5 segmentation yield the cord-normalized T2 signal
and the heterogeneity (texture) index; the cohort is derived and one-year outcome
change computed; the estimands are then obtained from covariate-adjusted change models
(HC3 robust standard errors), MCID logistic regression, a leg-pain negative control,
and multiplicity and fragility assessment. Anatomical panels are schematic and contain
no patient data.*

## Software environment

The analysis targets Python 3.11–3.13 (the continuous-integration matrix). Exact
dependency versions used to produce the committed results are pinned in
[`requirements.lock`](requirements.lock); the interpreter, operating system, and
package provenance are recorded in [`docs/ENVIRONMENT.md`](docs/ENVIRONMENT.md). The
pipeline performs no random number generation and is therefore deterministic: repeated
runs produce byte-identical `results/`, which `make verify` asserts.

## Reproducing the results

```bash
make setup                              # create .venv and install pinned dependencies
cp config.example.yaml config.yaml      # then set DATA_PATH to the local workbook
make repro                              # == python -m src.pipeline
make verify                             # run twice; assert results/ are identical
```

`make repro` reads the source workbook and regenerates every table in `results/`.
Because patient data are not distributed (see Data availability), full reproduction
requires authorized access to that workbook.

## Verifying the reported numbers without the data

To allow the analysis to be checked without access to protected data, the **aggregate
result tables** (model estimates only; no row-level data) are committed under
[`results/`](results). Every statistic reported in the manuscript is traced to a
specific `results/*.csv` cell and the function that produced it in
[`docs/NUMBERS_LEDGER.md`](docs/NUMBERS_LEDGER.md), and contested quantities are
independently re-derived in [`docs/STATS_VERIFICATION.md`](docs/STATS_VERIFICATION.md).
The unit tests exercise the full modeling stack on small synthetic frames and require
no patient data:

```bash
make test        # pytest on hand-constructed synthetic frames
make lint        # ruff
```

Continuous integration runs the tests and linter on every push
(`.github/workflows/ci.yml`).

## Repository layout

| Path | Contents |
| --- | --- |
| `src/data_loading.py` | Read the source workbook and flatten its two-row header |
| `src/cleaning.py` | Derive analysis variables; handle outliers and units |
| `src/cohort.py` | Assemble the analytic cohort and the attrition/flow counts |
| `src/analysis.py` | Change-score models, MCID logistic regression, negative control |
| `src/robustness.py` | Multiplicity, fragility, and IPW sensitivity analyses |
| `src/pipeline.py` | End-to-end orchestration (`python -m src.pipeline`) |
| `results/*.csv` | Committed aggregate estimates (no patient data) |
| `docs/CODE_WALKTHROUGH.md` | Line-by-line explanation of the analysis code |
| `docs/NUMBERS_LEDGER.md` | Each reported statistic mapped to its function and `results/` cell |
| `docs/STATS_VERIFICATION.md` | Independent re-derivation of contested quantities |
| `docs/DISCREPANCY_LOG.md` | Number-changing corrections and their effect |
| `docs/adr/` | Architecture decision records (normalization, texture, HC3, exploratory status) |
| `docs/ENVIRONMENT.md` | Interpreter, operating system, and dependency provenance |
| `PLAN.md` | Original pre-analysis plan, retained for provenance |

The `src/` modules that render figures are part of the reproducible pipeline; `make
repro` writes them to a local, git-ignored `figures/` directory.

## Data availability and ethics

The source dataset comprises imaging-derived muscle segmentations linked to
longitudinal patient-reported outcomes and contains protected health information. **No
patient data are stored in this repository.** The pipeline reads the workbook from a
local path defined in `config.yaml`, which is excluded from version control;
`.gitignore` additionally blocks tabular, spreadsheet, and imaging file formats as a
second safeguard. Investigators with appropriate approvals may obtain the dataset
through the study's data-governance process, as described in
[`DATA_AVAILABILITY.md`](DATA_AVAILABILITY.md). The study was approved by the
institutional review board with a waiver of informed consent.

## Citation and license

Please cite this software using the metadata in [`CITATION.cff`](CITATION.cff). The
code is released under the terms in [`LICENSE`](LICENSE).
