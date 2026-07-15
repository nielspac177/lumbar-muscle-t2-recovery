# Computational environment

The published results and figures were generated with the environment recorded
here. Exact pins are in [`requirements.lock`](../requirements.lock); looser,
forward-compatible ranges are in [`requirements.txt`](../requirements.txt),
[`pyproject.toml`](../pyproject.toml), and [`environment.yml`](../environment.yml).

## Reference environment

| Item | Value |
| --- | --- |
| Python | 3.13.5 (CPython) |
| OS (development) | macOS 26.1, arm64 (Apple Silicon) |
| pandas | 3.0.3 |
| numpy | 2.5.1 |
| scipy | 1.18.0 |
| statsmodels | 0.14.6 |
| matplotlib | 3.11.0 |
| seaborn | 0.13.2 |
| openpyxl | 3.1.5 |
| pyyaml | 6.0.3 |
| tableone | 0.9.6 |

## Determinism

The analysis uses **no random number generation** — no bootstrap, cross-validation,
resampling, or stochastic optimisation in the estimation path. All confidence
intervals are analytic (closed-form statsmodels covariance, plus a hand-coded
Wilson interval for proportions). Consequently, given the same input workbook the
pipeline is bit-for-bit reproducible; `make verify` runs it twice and diffs the
`results/` tables to confirm. See [`docs/adr/0003-hc3-robust-standard-errors.md`](adr/0003-hc3-robust-standard-errors.md).

## Reproducing the environment

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock      # exact pins used for the published results
# or, for a fresh compatible environment:
pip install -r requirements.txt
```

> Note: Python 3.14 on some Homebrew builds ships a broken `pyexpat`
> (`Symbol not found: _XML_SetAllocTrackerActivationThreshold`), which breaks
> matplotlib import. Python 3.11–3.13 are recommended.
