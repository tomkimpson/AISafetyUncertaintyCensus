PYTHON ?= python

.PHONY: all install test derived figures tables clean

all: derived figures tables

install:
	$(PYTHON) -m pip install -e ".[dev]"

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

clean:
	rm -f data/derived/*.csv
	rm -f paper/figures/ci_straddle.* paper/figures/uplift_straddle.*
	rm -f paper/tables/audit.tex paper/tables/census.tex paper/tables/census_counts.tex paper/tables/uplift.tex
