# Muscle T2 signal and recovery after lumbar decompression analysis code

This is the code behind the paper. It runs the analysis end to end, and it's public so
the results can be checked and rerun instead of being taken on trust. There's no patient dataset
and no manuscript here: just the pipeline, the tests, the pinned environment, the
aggregate result tables, and notes on why each modeling choice was made. The one image
is the methods overview below; its imaging panels come from a single de-identified
preoperative MRI.

## What the study looked at

A retrospective cohort at one academic center: 385 adults who had a lumbar
decompression and a usable preoperative MRI between 2016 and 2024, reported to STROBE.

The exposures are two MRI measures of the iliopsoas and deep back muscles. The first is
mean T2 signal divided by a central-canal reference on the same image, which keeps it
from riding on scanner and sequence settings. The second is a texture index for how
patchy that signal is. Both are standardized within the cohort. The outcomes are
one-year change in the Oswestry Disability Index and PROMIS Global Physical Health, and
whether each patient cleared that instrument's minimal clinically important difference
(MCID).

The models are change scores adjusted for age, sex, and baseline, with HC3 robust
standard errors; MCID attainment is logistic. Radicular leg pain is the negative
control, since it should not track muscle signal if the effect is real and local.
Holm and Benjamini–Hochberg correction, a fragility index, and
inverse-probability-of-attrition weighting are all included as sensitivity checks.

One thing to be clear about: the T2-signal analysis came after a prespecified volume
analysis that was null. So it is post-hoc, and the findings are hypothesis-generating
rather than confirmatory. The code and the decision records under `docs/adr/` say so
plainly.

## Methods overview

![Study methodology overview: preoperative axial T2 MRI and L3–L5 segmentation; cord-normalized T2 signal and a heterogeneity index; cohort derivation and 1-year outcome change; adjusted change models with HC3 robust standard errors, MCID logistic regression, a leg-pain negative control, and multiplicity and fragility assessment.](docs/img/methods_overview.png)

*From preoperative axial T2 MRI and L3–L5 segmentation to the cord-normalized signal
and heterogeneity index, then cohort derivation and one-year outcome change, then the
adjusted change models, MCID logistic regression, the leg-pain negative control, and
the multiplicity and fragility checks. The imaging panels come from a single
de-identified preoperative MRI.*

## Running it

```bash
make setup                              # create .venv and install the pinned dependencies
cp config.example.yaml config.yaml      # then point DATA_PATH at the local workbook
make repro                              # == python -m src.pipeline
make verify                             # run twice and confirm results/ are identical
```

`make repro` reads the workbook and rebuilds everything under `results/`. You need the
actual dataset for that, which is not in the repo (see below). Nothing in the pipeline
draws on a random number generator, so two runs produce identical files; `make verify`
is just that check made explicit. The interpreter and exact package versions used for
the committed numbers are in `requirements.lock` and `docs/ENVIRONMENT.md`.

## Checking the numbers without the data

You don't need the dataset to audit the results. The aggregate estimates, with no
row-level data, are committed under `results/`, and every number in the paper points
back to a specific cell and function in `docs/NUMBERS_LEDGER.md`. The contested ones are
re-derived from scratch in `docs/STATS_VERIFICATION.md`. The tests run the full set of
models on small hand-built frames, so they need no patient data:

```bash
make test        # pytest
make lint        # ruff
```

CI runs both on every push.

## What's where

| Path | Contents |
| --- | --- |
| `src/data_loading.py` | Read the source workbook and flatten its two-row header |
| `src/cleaning.py` | Derive the analysis variables; handle outliers and units |
| `src/cohort.py` | Build the analytic cohort and the attrition/flow counts |
| `src/analysis.py` | Change-score models, MCID logistic regression, negative control |
| `src/robustness.py` | Multiplicity, fragility, and IPW sensitivity analyses |
| `src/pipeline.py` | Runs the whole thing (`python -m src.pipeline`) |
| `results/*.csv` | Committed aggregate estimates, no patient data |
| `docs/CODE_WALKTHROUGH.md` | The analysis code explained, line by line |
| `docs/NUMBERS_LEDGER.md` | Each reported number tied to its function and `results/` cell |
| `docs/STATS_VERIFICATION.md` | Independent re-derivation of the contested numbers |
| `docs/DISCREPANCY_LOG.md` | Corrections that moved a number, and by how much |
| `docs/adr/` | Why each choice was made (normalization, texture, HC3, exploratory status) |
| `docs/ENVIRONMENT.md` | Interpreter, OS, and dependency provenance |
| `PLAN.md` | The original pre-analysis plan, kept for provenance |

The figure-drawing modules under `src/` are part of the pipeline; `make repro` writes
their output to a local `figures/` directory that git ignores.

## Data and ethics

The dataset is muscle segmentations linked to patient-reported outcomes, so it is
protected health information and stays out of the repository. The pipeline reads it from
a local path set in `config.yaml`, which is git-ignored, and `.gitignore` also blocks
spreadsheet and imaging formats as a backstop. Investigators with the appropriate
approvals can obtain the data through the study's governance process, described in
`DATA_AVAILABILITY.md`. The study was approved by the institutional review board with a
waiver of consent.

## Citation and license

Cite it with the metadata in `CITATION.cff`. The code is released under `LICENSE`.
