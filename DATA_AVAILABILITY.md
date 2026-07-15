# Data availability

This repository is **code-only**. The patient dataset — imaging-derived muscle
segmentations linked to longitudinal patient-reported outcomes — contains protected
health information and is **not** distributed here, in any form (no raw data, no
de-identified extract, no synthetic surrogate).

## What is and is not in this repository

- **Included:** all analysis code (`src/`), tests on tiny hand-mocked frames
  (`tests/`), aggregate result tables containing only model estimates
  (β/OR/CI/P/n; `results/` are regenerated, not committed), figures, and full
  methodological documentation (`docs/`, including `docs/adr/`).
- **Excluded:** the source workbook and any file that could contain PHI. The
  analysis reads the workbook from a local absolute path set in `config.yaml`,
  which is gitignored; `.gitignore` additionally blocks all tabular, spreadsheet,
  and imaging formats as a second safeguard.

## Reproducing the results

Investigators with the appropriate institutional approvals can obtain the dataset
through the study's data-governance process at Beth Israel Deaconess Medical
Center. With the workbook in place and `config.yaml` pointing to it, a single
command (`make repro`, i.e. `python -m src.pipeline`) regenerates every table in
`results/` and every figure in `figures/`. The pipeline uses no random number
generation and is bit-for-bit reproducible (`make verify`). Every reported number
is traced to code and output in [`docs/NUMBERS_LEDGER.md`](docs/NUMBERS_LEDGER.md).

## Correspondence

Requests regarding the code should be directed to the repository author; requests
regarding data access should follow the institutional data-governance process.
