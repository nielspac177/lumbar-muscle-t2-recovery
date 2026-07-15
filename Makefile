# One-command reproduction for the lumbar-muscle-pro analysis.
# Requires a config.yaml (copy from config.example.yaml and set DATA_PATH).
PYTHON ?= python

.PHONY: help setup repro test lint verify clean

help:
	@echo "make setup   - create .venv and install pinned dependencies"
	@echo "make repro    - run the full pipeline (regenerates results/)"
	@echo "make test     - run the unit test suite (no patient data needed)"
	@echo "make lint     - run ruff static checks"
	@echo "make verify   - run the pipeline twice and assert identical results/ (determinism)"
	@echo "make clean    - remove generated results/ and figures/ (keeps .gitkeep)"

setup:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.lock pytest ruff

repro:
	$(PYTHON) -m src.pipeline

test:
	$(PYTHON) -m pytest

lint:
	ruff check src tests

verify:
	@rm -rf /tmp/_repro_run1
	@echo "Run 1..." && $(PYTHON) -m src.pipeline >/dev/null && cp -r results /tmp/_repro_run1
	@echo "Run 2..." && $(PYTHON) -m src.pipeline >/dev/null
	@diff -rq /tmp/_repro_run1 results && echo "DETERMINISM OK: results/ identical across two runs" || (echo "NON-DETERMINISTIC OUTPUT" && exit 1)
	@rm -rf /tmp/_repro_run1

clean:
	find results -type f ! -name '.gitkeep' -delete
	find figures -type f ! -name '.gitkeep' -delete 2>/dev/null || true
