# Contributing

This repository accompanies a research publication and is maintained primarily for
reproducibility. Issues and pull requests that improve correctness, reproducibility,
or documentation are welcome.

## Development setup

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest ruff
```

## Before opening a pull request

- `make test` — the unit suite must pass (uses tiny mocked frames; no data needed).
- `make lint` — `ruff` must be clean.
- `make verify` — if you touch the analysis, confirm the pipeline is still
  deterministic (two runs produce identical `results/`).
- **Never commit patient data.** All tabular/spreadsheet/imaging formats are
  gitignored; keep it that way. Tests must not depend on real data.
- Document any non-obvious methodological change as an ADR in `docs/adr/`.

## Scope

Changes that alter reported statistical estimates should be accompanied by an update
to `docs/NUMBERS_LEDGER.md` and `docs/DISCREPANCY_LOG.md` so the published figures
and manuscript remain traceable.
