# AI Safety Uncertainty Census

Reproduction code and data for the manuscript *"Thresholds Without Error Bars: A Statistical Audit of Frontier AI Safety Evaluations"* ([LaTeX source](paper/main.tex)).

The paper assembles a structured corpus of 96 eligible, source-reported dangerous-capability records from 26 public documents across Anthropic, OpenAI, Google DeepMind, METR, UK AISI, and Apollo. Eighty-one records report no uncertainty. A conditional model-level audit uses a one-sided 95% rule: 2/6 direct-count results are unresolved, while four SWE-bench results yield 2/4 under a task-level convention and 1/4 under a run-level convention. These are explicit IID working models, not claims that the public designs identify a unique sampling distribution. A separate Opus 4 bio-uplift reconstruction retains the supplementary 2.8× line under all three conventional readings considered and all nine allowed control/treatment arm-size combinations.

All numbers in this repository are published aggregate statistics taken from public system cards and evaluation reports; no dual-use content is included. Source provenance (canonical URLs, retrieval dates, SHA-256 hashes) is recorded in [`data/raw/sources/MANIFEST.md`](data/raw/sources/MANIFEST.md).

## Repository layout

```
src/evalaudit/     Python package: proportion CIs, Bayesian posterior, cluster
                   corrections, power analysis, ratio (Fieller/delta/bootstrap) CIs
scripts/           Pipeline entry points (see below)
tests/             Unit tests for every evalaudit module against reference values
data/raw/          Canonical census_records.csv, model-level evals.csv,
                   legacy census_full.md, and sources/MANIFEST.md
data/derived/      Pipeline outputs (committed for convenience; fully regenerable)
paper/figures/     Generated figures (ci_straddle, uplift_straddle)
paper/tables/      Generated LaTeX tables (audit, census, census_counts, uplift)
paper/             Manuscript source
```

## Getting started

Requires Python ≥ 3.10. The environment is pinned with [uv](https://docs.astral.sh/uv/)
(`uv.lock`) for reproducible installs:

```bash
uv sync --extra dev        # exact pinned environment from uv.lock
uv run pytest              # correctness tests
```

Without uv, `pip install -e ".[dev]"` works from the bounded ranges in `pyproject.toml`
(unpinned; prefer uv for reproducibility).

Reproduce everything (derived CSVs, figures, tables) with one command:

```bash
make all
```

or run the pipeline steps manually, in dependency order:

```bash
python scripts/uplift_analysis.py     # -> data/derived/uplift_readings.csv
python scripts/coverage_sim.py        # -> data/derived/coverage_sim.csv (20k-replicate simulation)
python scripts/run_audit.py           # -> data/derived/audited.csv, icc_sweep.csv, verdict_grid.csv
python scripts/make_figure.py         # -> paper/figures/ci_straddle.{pdf,png}
python scripts/make_uplift_figure.py  # -> paper/figures/uplift_straddle.{pdf,png}
python scripts/make_tables.py         # -> paper/tables/*.tex
```

All stochastic steps use fixed seeds, so outputs are bit-reproducible up to floating-point/library differences.

## Reproducibility & verification

Two separate claims, documented in [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md):

- **The analysis is procedurally reproducible.** `make all` regenerates every derived CSV,
  figure, and table from the census inputs with fixed seeds. `make verify` runs the tests,
  re-resolves every cited source, checks the derived-data checksums, and runs a guard
  (`scripts/check_paper_numbers.py`) that fails if a number hand-transcribed into the
  manuscript drifts from the derived CSVs.
- **The structured corpus is archivally auditable.** It was built and recoded with AI assistance
  (see [`data/raw/sources/CONSTRUCTION.md`](data/raw/sources/CONSTRUCTION.md)), so it is not
  bit-reproducible; instead every cited source is pinned in
  [`MANIFEST.md`](data/raw/sources/MANIFEST.md) (SHA-256 for PDFs, Wayback for HTML) and
  re-checkable with `python scripts/verify_sources.py`, and every cited value is tracked
  against its primary source in `data/verification/cell_audit.csv`. Explicit eligibility,
  denominator, and uncertainty coding lives in `data/raw/census_records.csv`.

The submission gate is explicit: `data/verification/human_signoff.csv` lists every eligible
record and remains `pending` until the author performs row-by-row sign-off. The manuscript
does not claim completed human verification while that file is pending.

## License

MIT — see [LICENSE](LICENSE).
