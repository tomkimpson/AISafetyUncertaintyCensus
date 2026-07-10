# AI Safety Uncertainty Census

Reproduction code and data for the paper *"Do Frontier-Safety Evaluations Have the Resolving Power Their Thresholds Imply?"* (manuscript in preparation; the LaTeX source will be added to `paper/` and a link posted here once it is on arXiv).

The paper takes a census of governance-relevant dangerous-capability evaluation results across four frontier-safety framework families (Anthropic RSP, OpenAI Preparedness, Google DeepMind FSF, and third-party evaluators such as METR, UK AISI, and Apollo). Published evaluations rarely report quantified uncertainty, yet comparing a score against a capability threshold is an implicit hypothesis test. Auditing the nine machine-auditable Bernoulli rows shows that five cannot statistically resolve their own threshold at the 95% level, and a case study of the Opus 4 bio-uplift trial (2.53× observed vs a 2.8× threshold) shows the comparison central to an ASL-3 deployment decision cannot be resolved with the published sample sizes.

All numbers in this repository are published aggregate statistics taken from public system cards and evaluation reports; no dual-use content is included. Source provenance (canonical URLs, retrieval dates, SHA-256 hashes) is recorded in [`data/raw/sources/MANIFEST.md`](data/raw/sources/MANIFEST.md).

## Repository layout

```
src/evalaudit/     Python package: proportion CIs, Bayesian posterior, cluster
                   corrections, power analysis, ratio (Fieller/delta/bootstrap) CIs
scripts/           Pipeline entry points (see below)
tests/             Unit tests for every evalaudit module against reference values
data/raw/          Census inputs: evals.csv (auditable rows), census_full.md
                   (full census), sources/MANIFEST.md (provenance)
data/derived/      Pipeline outputs (committed for convenience; fully regenerable)
paper/figures/     Generated figures (ci_straddle, uplift_straddle)
paper/tables/      Generated LaTeX tables (audit, census, census_counts, uplift)
paper/             Manuscript source will live here
```

## Getting started

Requires Python ≥ 3.10. The environment is pinned with [uv](https://docs.astral.sh/uv/)
(`uv.lock`) for reproducible installs:

```bash
uv sync --extra dev        # exact pinned environment from uv.lock
uv run pytest              # 39 correctness tests
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
- **The census is archivally reproducible.** It was built by an AI-assisted research pass
  (see [`data/raw/sources/CONSTRUCTION.md`](data/raw/sources/CONSTRUCTION.md)), so it is not
  bit-reproducible; instead every cited source is pinned in
  [`MANIFEST.md`](data/raw/sources/MANIFEST.md) (SHA-256 for PDFs, Wayback for HTML) and
  re-checkable with `python scripts/verify_sources.py`, and every cited value is tracked
  against its primary source in `data/verification/cell_audit.csv`.

As of the latest verification pass: all 16 cited sources resolve; the nine machine-auditable
rows and the Opus 4 bio-uplift case study are confirmed page-level against the source cards;
and all 48 bibliography entries resolve and match.

## License

MIT — see [LICENSE](LICENSE).
