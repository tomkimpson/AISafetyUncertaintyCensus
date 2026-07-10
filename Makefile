PYTHON ?= python

.PHONY: all install test derived figures tables clean \
        verify verify-sources verify-derived check-numbers checksums

all: derived figures tables

# Reproducible install from the committed lockfile (uv). Falls back to pip+pyproject
# for environments without uv (unpinned; prefer `uv sync`).
install:
	uv sync --extra dev || $(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

derived:
	$(PYTHON) scripts/uplift_analysis.py
	$(PYTHON) scripts/coverage_sim.py
	$(PYTHON) scripts/run_audit.py

figures: derived
	$(PYTHON) scripts/make_figure.py
	$(PYTHON) scripts/make_uplift_figure.py

tables: derived
	$(PYTHON) scripts/make_tables.py

# --- verification -------------------------------------------------------------
# Full verification suite: tests, source provenance, derived checksums, and the
# paper-number drift guard.
verify: test verify-sources verify-derived check-numbers

# Resolve, hash, and Wayback-archive every cited source (writes
# data/verification/source_provenance.csv). Requires network.
verify-sources:
	$(PYTHON) scripts/verify_sources.py

# Regenerate the per-cell claim-fidelity log skeleton (preserving recorded
# confirmations) so it stays in sync with the census.
seed-audit:
	$(PYTHON) scripts/seed_cell_audit.py

# Check committed derived CSVs against recorded SHA-256. Exact match holds on the
# same platform; floating-point/BLAS differences across platforms can change the
# simulation columns (coverage_sim.csv) in the last digits — regenerate and diff
# numerically if a mismatch is platform-related (see docs/REPRODUCIBILITY.md).
verify-derived:
	cd data/derived && shasum -c CHECKSUMS.sha256

# Recompute the checksum file after an intentional pipeline change.
checksums:
	cd data/derived && shasum -a 256 *.csv > CHECKSUMS.sha256

# Guard: numbers hand-transcribed into paper/main.tex still match the derived CSVs.
check-numbers:
	$(PYTHON) scripts/check_paper_numbers.py

clean:
	rm -f data/derived/*.csv
	rm -f paper/figures/ci_straddle.* paper/figures/uplift_straddle.*
	rm -f paper/tables/audit.tex paper/tables/census.tex paper/tables/census_counts.tex paper/tables/uplift.tex
