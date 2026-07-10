# Reproducibility & verification runbook

This repository has two independent reproducibility claims. Keep them separate:

1. **The analysis is procedurally reproducible.** Given the census inputs, the statistics,
   figures, and tables regenerate deterministically (fixed seeds, pinned environment).
2. **The census is archivally reproducible, not procedurally.** It was built by an
   AI-assisted research pass that cannot be bit-reproduced (see
   [`data/raw/sources/CONSTRUCTION.md`](../data/raw/sources/CONSTRUCTION.md)); instead every
   cited source is pinned and every cited value is checkable against it.

## 1. Reproduce the analysis (fully automated)

```bash
uv sync --extra dev        # install the exact pinned environment from uv.lock
uv run pytest              # 39 correctness tests against hand-computed references
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

## 2. Re-verify the census against primary sources

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

### 2b. Claim fidelity (agent-fetched, human-signed)

`data/verification/cell_audit.csv` holds one row per census entry with the claimed
(threshold, n, score, uncertainty, direction), the cited locator, a `value_status`, and a
confirming quote. Regenerate the skeleton (preserving recorded confirmations) with:

```bash
python scripts/seed_cell_audit.py
```

Verification status: **all 98 census rows have been checked against their primary sources**
(86 `confirmed`, 12 `confirmed_note`; no `unverified`, `mismatch`, or `unresolved` rows
remain). The verification was originally staged by audit impact, and that ordering still
explains where the strongest evidence lies:

- **Tier 0 — headline.** The nine `evals.csv` rows + the Opus 4 bio-uplift case study,
  confirmed page-level against the source PDFs. These carry the paper's central claims.
- **Tier 1 — rest of Anthropic.** Confirmed page-level.
- **Tiers 2–3 — OpenAI / DeepMind / third-party / post-2025 rows.** Confirmed against the
  cited locator in each source; do not affect the nine-row headline.

**Sign-off is complete when** `cell_audit.csv` has no `mismatch` or `unresolved` rows; any
residual `confirmed_note` (faithful to the cited source but carrying a documented caveat —
e.g. the 17-vs-18/33 cross-card discrepancy, or a value the source states only in a summary
table) is an accepted disposition. As of the latest pass this criterion is met.

### 2c. Bibliography (automated)

The academic references in `paper/references.bib` are covered by the `check-refs` and
`check-arxiv-llm-compliance` skills (arXiv/DOI/Semantic Scholar resolution + author/title
match). As of 2026-07-10 all 48 entries resolve and match; the one defect found (wrong author
first names in `stelling2025evaluating`) is fixed.

## Coverage gaps (stated, not hidden)

- The reference-checking skills cover the ~15 academic arXiv/DOI references. The ~25
  **vendor/institutional sources** (system cards, framework docs) have no DOI/arXiv record and
  are covered **only** by `verify_sources.py` (existence + hash/Wayback) and `cell_audit.csv`
  (claim fidelity).
- Vendor PDFs are **not committed** (copyright); `MANIFEST.md` + hashes + Wayback are the
  archival stand-in. Local copies cache under `data/verification/cache/` (gitignored).
