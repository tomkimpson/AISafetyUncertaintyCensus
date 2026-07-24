# AI Safety Uncertainty Census

Reproduction code and data for the manuscript *"Thresholds Without Error Bars: A Statistical Audit of Frontier AI Safety Evaluations"* ([LaTeX source](paper/main.tex)).

The paper assembles a structured corpus of 96 eligible, source-reported
dangerous-capability records from 21 contributing result documents within a fixed
26-document frame across Anthropic, OpenAI, Google DeepMind, METR, UK AISI, and Apollo.
Eighty-one records report no uncertainty; 13/21 contributing documents report none for any
eligible record. A conditional model-level audit uses two separate one-sided 95% claims and
a three-way class (below demonstrated / indeterminate / above demonstrated): the six
direct-count results yield 3/2/1, while four SWE-bench results yield 2/2/0 under a
task-level convention and 3/1/0 under a run-level convention. The two directional claims
are each controlled at α=.05; together they are not one simultaneous 95% classification.
These are explicit IID working models, not claims that the public designs identify a unique
sampling distribution. A separate Opus 4 bio-uplift illustration retains the supplementary
2.8× line under all three conventional readings considered and all nine allowed
control/treatment arm-size combinations.

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
data/verification/ AI-assisted claim audit plus pending two-human validation templates
paper/figures/     Generated figures (ci_straddle, uplift_straddle)
paper/tables/      Generated LaTeX tables (audit, reporting levels, census, uplift)
docs/              Reproduction, human-validation, and right-of-reply protocols
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
python scripts/summarize_corpus.py     # -> record/source-document reporting summaries
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
  denominator, and uncertainty coding lives in `data/raw/census_records.csv`. The cross-check
  is AI-assisted (performed independently of the original extraction), not human sign-off.

Before journal submission, two independent humans must recode all screened records and all
ten model-level reconstructions, followed by adjudication. The templates and instructions
are in [`docs/HUMAN_VALIDATION_PROTOCOL.md`](docs/HUMAN_VALIDATION_PROTOCOL.md);
`make verify-human` intentionally fails until they are complete. Developer factual review
and right-of-reply are separately specified in
[`docs/RIGHT_OF_REPLY.md`](docs/RIGHT_OF_REPLY.md). Neither gate is represented as completed
by this repository revision. The full handoff is in
[`docs/SUBMISSION_CHECKLIST.md`](docs/SUBMISSION_CHECKLIST.md).

## License

MIT — see [LICENSE](LICENSE).
