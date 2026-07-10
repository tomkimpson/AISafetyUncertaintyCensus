# How the census was constructed

This documents how `census_full.md` and `evals.csv` were produced, so a third party can
judge and re-verify them. It is deliberately honest about what is and is not reproducible.

## What the census is

A hand-curated table of **governance-relevant dangerous-capability evaluation results**
drawn from public frontier-safety frameworks and vendor model/system cards. 98 rows span the
Claude 4 / Gemini 2.5 / GPT-4.x generation through the GPT-5.6 Preview card of June 2026.
`census_full.md` is the archival record; `evals.csv` is the machine-auditable subset (the
nine rows that pair an integer pass count with an operative numeric threshold).

## How it was built (and why it is not bit-reproducible)

The census was assembled by an **AI-assisted research pass** (a language model with web/PDF
access) over the public documents listed in `MANIFEST.md`, followed by manual review and
correction. That generation step is **inherently non-deterministic**: it had no fixed seed,
prompt log, or tool trace, and re-running a model would not reproduce the table byte-for-byte.
We therefore do **not** claim procedural reproducibility for census *construction*.

What we do provide, and what a third party can check, is **archival reproducibility**:

1. **Fixed sources.** Every cited document is pinned in `MANIFEST.md` by canonical URL plus a
   stable SHA-256 (PDFs) or a dated Wayback snapshot (HTML). `scripts/verify_sources.py`
   re-resolves and re-hashes them into `data/verification/source_provenance.csv`.
2. **Claim fidelity.** `data/verification/cell_audit.csv` records, per census row, whether the
   cited value was confirmed against the primary source at the cited section/page, with a
   confirming quote. This is the reproducible check that replaces "trust the model."

So the census is re-derivable **from fixed documents by a human or agent following the coding
rules below** — not by re-running an opaque generation.

## Inclusion criterion

A row is included iff it is **governance-relevant**: an evaluation a framework uses to make a
safety-relevant decision about a model's capability or deployment (a score checked against a
threshold, or mapped to a capability level / ASL / CCL tier). A bioweapons-knowledge score
measured against a threshold is in; a general benchmark (MMLU, a coding leaderboard) reported
in the same card but tied to no safety decision is out. (Same wording as `main.tex` §census.)

## Field definitions

| field | meaning |
|---|---|
| framework | RSP (Anthropic) / PF (OpenAI) / FSF (DeepMind) / third-party |
| domain / capability | the evaluated capability (CBRN, autonomy, cyber, persuasion, …) |
| model | the evaluated model(s); a cell may bundle models ("Opus 4 / Sonnet 4") |
| threshold | the operative go/no-go line — numeric where one exists, else the prose tier |
| n | sample size (tasks / questions / trials / participants), or `NOT REPORTED` |
| score | the reported figure, verbatim in the units the source uses |
| CI / uncertainty | the source's uncertainty cell, verbatim; `none` if absent |
| direction | which side of the threshold the source places the result |
| citation | document + section/page |
| is_illustrative (evals.csv) | `0` for real census numbers; `1` reserved for demo rows (none currently) |

## Coding rules for ambiguous cases

These are the judgment calls a re-coder must reproduce:

- **Unlabelled dispersion.** Where a source gives "±x%" with no statement of whether it is an
  SD, SE, or CI (e.g. Anthropic's uplift "±13%"), the value is recorded verbatim in the
  uncertainty cell and classified as a *bare ±*, **not** a proper interval. The uplift case
  study propagates every admissible reading rather than guessing one.
- **NOT REPORTED n.** A row counts as reporting a sample size iff its `n` cell contains a
  digit; a bare "NOT REPORTED" is the only n-absent pattern.
- **Proper interval vs bare ±.** "Proper" means a CI / credible interval / bootstrap CI /
  error bar with a stated coverage; a bare "±" is not. (`make_tables.py:_has_uncertainty` /
  `_is_proper_interval` implement this split; the headline counts derive from it.)
- **Score units left as reported.** Percentages, medians, pass@k, correlations, and integer
  pass counts are kept in their source units; only rows expressible as an integer count over a
  Bernoulli denominator enter `evals.csv` as auditable.
- **Cross-source discrepancies.** Where two vendor documents disagree (e.g. the Opus 4 card
  states Claude 3.7 scored 18/33 on bioweapons knowledge while the 3.7 card itself states
  17/33), the census records the value from the document it cites and flags the discrepancy
  in `cell_audit.csv` rather than silently picking one.
- **Generation label.** The "Post-2025 generation" heading is a label only; those rows are
  part of the single 98-row population and its headline counts (see `census_full.md`).

## Known soft spots (carried from the research pass)

Recorded in the "Caveats" section of `census_full.md` and, per row, in `cell_audit.csv`:
two GPT-4o cells read via an HTML summarizer rather than the raw PDF; some Apollo
percentages not machine-verifiable; the unlabelled "±" ambiguity above. These are disclosed,
not hidden.
