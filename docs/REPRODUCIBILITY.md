# Reproducibility & verification runbook

This repository has two independent reproducibility claims and one human-validation gate.
Keep them separate:

1. **The analysis is procedurally reproducible.** Given the census inputs, the statistics,
   figures, and tables regenerate deterministically (fixed seeds, pinned environment).
2. **The structured corpus is archivally auditable, not procedurally reproducible.** It was built and recoded through
   AI-assisted research pass that cannot be bit-reproduced (see
   [`data/raw/sources/CONSTRUCTION.md`](../data/raw/sources/CONSTRUCTION.md)); instead every
   cited source is pinned and every cited value is checkable against it.

## 1. Reproduce the analysis (fully automated)

```bash
uv sync --extra dev        # install the exact pinned environment from uv.lock
uv run pytest              # correctness tests against reference values
uv run make all            # regenerate data/derived/*, paper/figures/*, paper/tables/*
uv run make verify-derived # committed derived CSVs match data/derived/CHECKSUMS.sha256
uv run make check-numbers  # numbers hand-typed into paper/main.tex still match the CSVs
```

- Dependencies are pinned in `pyproject.toml` (bounded ranges) and `uv.lock` (exact). CI
  runs this on Python 3.11 and 3.13.
- `make all` = `derived` → `figures` → `tables`. The derived CSVs are committed for
  convenience and are regenerable.
- **Same-platform** regeneration is byte-identical, so `verify-derived` (SHA-256) passes. The
  simulation file `coverage_sim.csv` can differ in its last digits across BLAS/threading
  implementations; if `verify-derived` fails only on that file across platforms, regenerate
  and compare numerically — the reported results are robust to those last-digit differences
  (the paper rests on the qualitative straddle verdict, not on coverage point estimates).
- `make check-numbers` closes the loop on the three derived CSVs that are *not* `\input` into
  the manuscript (`verdict_grid.csv`, `coverage_sim.csv`, and the ±1 sensitivity in
  `audited.csv`): their figures reach the paper as prose, and this guard fails if that prose
  drifts from the data.

The derived stage also writes `corpus_reporting_levels.csv` and
`source_reporting.csv`. These keep record weighting distinct from source-document weighting;
neither should be treated as probability-sample inference.

## 2. Re-verify the structured corpus against primary sources

### 2a. Source provenance (automated)

```bash
python scripts/verify_sources.py   # stdlib only; needs network
```

Writes `data/verification/source_provenance.csv`: for every source in
[`MANIFEST.md`](../data/raw/sources/MANIFEST.md) it records resolve status, SHA-256, and a
Wayback snapshot. Expect **26/26 resolve**.

- **PDF sources** have a stable SHA-256 — the recorded hash must match on re-download. The
  Opus 4 System Card (the case study's source) matches the hash first recorded on 2026-07-03.
- **HTML sources** return different bytes per fetch (dynamic markup), so they are **not**
  pinned by SHA; cite the **Wayback snapshot** URL from the provenance CSV instead.

### 2b. AI-assisted claim fidelity

`data/verification/cell_audit.csv` holds one row per screened record with the claimed
(threshold, n, score, uncertainty, direction), the cited locator, a `value_status`, and a
confirming quote. Regenerate the skeleton (preserving recorded confirmations) with:

```bash
python scripts/seed_cell_audit.py
```

The cell-audit statuses are an AI-assisted claim-fidelity pass performed independently of the
original extraction, not human sign-off. The canonical analysis input is
`data/raw/census_records.csv`, which additionally records eligibility, denominator status,
and uncertainty class. The staging explains where the most detailed source checks lie:

- **Tier 0 — central reconstructions.** The ten model-level `evals.csv` rows (nine source
  records because A4 maps to two models) plus the Opus 4 bio-uplift case study.
- **Tier 1 — rest of Anthropic.** Confirmed page-level.
- **Tiers 2–3 — OpenAI / DeepMind / third-party / post-2025 rows.** Cross-checked against
  the cited locator in each source.

### 2c. Independent human-validation gate

Read [`HUMAN_VALIDATION_PROTOCOL.md`](HUMAN_VALIDATION_PROTOCOL.md), then have two human
coders independently complete the census and model-audit templates and adjudicate every
row. Seed missing blank files without overwriting existing work:

```bash
python scripts/seed_human_validation.py
make verify-human
```

`make verify-human` is expected to fail while any row is `pending`. It validates allowed
categories, checks source-confirmation flags and row coverage, and reports raw agreement
plus Cohen's kappa once complete. Passing this gate does not automatically update the
canonical CSVs: adjudicated differences must be reviewed, applied, regenerated, and tested.

The external factual-review process is separate and documented in
[`RIGHT_OF_REPLY.md`](RIGHT_OF_REPLY.md). A non-response is not validation.

### 2d. Bibliography (automated)

Academic references in `paper/references.bib` should be checked by arXiv/DOI resolution and
author/title matching before submission. The July 2026 revision adds STREAM, NIST AI 800-3,
Evaluation Cards, California SB-53, and the EU GPAI Code of Practice to make the novelty and
regulatory context explicit; their canonical identifiers are stored in the bibliography.

## Coverage gaps (stated, not hidden)

- The reference-checking skills cover the ~15 academic arXiv/DOI references. The ~25
  **vendor/institutional sources** (system cards, framework docs) have no DOI/arXiv record and
  are covered **only** by `verify_sources.py` (existence + hash/Wayback) and `cell_audit.csv`
  (claim fidelity).
- Vendor PDFs are **not committed** (copyright); `MANIFEST.md` + hashes + Wayback are the
  archival stand-in. Local copies cache under `data/verification/cache/` (gitignored).
