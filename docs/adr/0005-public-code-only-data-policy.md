# ADR 0005 — Public, code-only repository; no patient data

- **Status:** Accepted
- **Date:** 2026-07-08

## Context
The dataset links imaging-derived muscle segmentations to longitudinal
patient-reported outcomes and therefore contains protected health information
(PHI). The study is intended for a reproducible public release accompanying a
JAMA Network submission, but patient data cannot be shared.

## Decision
The repository is **public and code-only**:
- The analysis reads the source workbook from a local absolute path defined in
  `config.yaml`, which is **gitignored**; `config.example.yaml` ships a generic
  placeholder path.
- `.gitignore` additionally blocks all tabular/spreadsheet/imaging formats
  (`*.xlsx`, `*.csv`, `*.dcm`, `data/`, …) as a second safeguard.
- Tests use **tiny hand-mocked frames** built in code (`tests/conftest.py`); there
  is no synthetic fixture generator and no derived patient data of any kind.
- The published `results/` CSVs contain only aggregate model estimates
  (β/OR/CI/p/n), never row-level data.
- Commits are authored **solely by the study author**; no automated co-author
  trailer is added.

## Consequences
- A reviewer or reader can inspect and re-run all analysis logic, and reproduce
  every figure/table given authorized access to the data through the study's
  data-governance process (`DATA_AVAILABILITY.md`).
- CI runs on mocked frames only, so it can be public without exposing PHI.
- Before the repo is made public, a full-history secret/PHI sweep is run
  (WP-A8); history is scrubbed with `git filter-repo` if anything is found.
