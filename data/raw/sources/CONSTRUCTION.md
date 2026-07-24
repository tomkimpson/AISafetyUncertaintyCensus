# How the structured corpus was constructed

This document defines the sampling frame, record unit, eligibility rules, and coding fields
for `data/raw/census_records.csv`. It distinguishes reproducible analysis from an
AI-assisted research pass that is not bit-reproducible.

## Sampling frame and cutoff

The fixed frame is the 26 version-pinned public documents in `MANIFEST.md`, retrieved and
screened through 30 June 2026. Twenty-two are result documents screened for candidate
records. Twenty-one contribute at least one primary-eligible record; the HCAST paper
contributes only excluded benchmark-description record T7. The other four documents
(Anthropic's RSP, the Gemini 3 Pro model card, the RAND uplift study, and the Epoch
commentary) supply framework, threshold, or comparison context rather than census
candidate records. The frame covers Anthropic RSP system cards, OpenAI Preparedness system
cards, Google DeepMind FSF reports, and public METR, UK AISI, and Apollo reports. This is
purposive coverage of the listed framework families, not an exhaustive population of all
dangerous-capability evaluations.

The screen produced 98 candidate records. The primary corpus contains 96 eligible records.
Two remain in the canonical file with `include_primary=false` and an explicit reason:

- T7 is a benchmark description without an evaluated-model result.
- A32 was explicitly excluded from the source's RSP determination.

`census_full.md` is retained as the legacy narrative extraction, not as the canonical input.

## Record unit

A record is one source-reported table row or prose result whose score is mapped to a
safety-relevant capability or deployment determination. Source display granularity is
preserved. A record may therefore bundle models or metrics when the source gives no
disaggregation. The corpus supports an analysis of reporting practice; its rows are not
asserted to be independent evaluation outcomes.

The model-level threshold audit has a different unit. `evals.csv` expands shared source
record A4 into separate Opus 4 and Sonnet 4 results, so it contains ten model-level results.
Both retain `record_id=A4`; this makes the one-to-many mapping explicit.

## Canonical fields and coding rules

`census_records.csv` carries the source text plus explicit analysis fields:

| field | rule |
|---|---|
| `record_id` | Stable framework letter plus source-row number. |
| `include_primary` | `true` only when the record meets the governance-relevance rule. |
| `exclusion_reason` | Required for screened records excluded from the primary corpus. |
| `n_status` | `score_denominator`, `partial_or_indirect`, or `not_reported`. |
| `uncertainty_class` | `proper_interval`, `bare_dispersion`, or `none`. |
| `source_id` | Key into the pinned-source manifest. |

A score denominator is a count tied to the displayed score. Numerical information such as
“over 100 attempts” is `partial_or_indirect` when it does not identify that denominator.
This replaces the legacy rule that treated any digit in the `n` cell as a reported sample
size.

A proper interval states an inferential construction and coverage or credibility level. An
unlabelled “±” is a bare dispersion, not an interval. Percentages, medians, pass@k,
correlations, and counts remain in source units. Cross-source discrepancies remain attached
to their source record and are documented in `data/verification/cell_audit.csv`.

## Reproducibility and verification

The initial extraction and later recoding were AI-assisted and had no fixed prompt/tool log,
so corpus construction is not procedurally reproducible. The repository instead provides:

1. version-pinned sources in `MANIFEST.md`;
2. stable record IDs and source locators in `census_records.csv`; and
3. claim-fidelity notes in `data/verification/cell_audit.csv`.

The cell-audit cross-check is AI-assisted (performed independently of the original
extraction), not human sign-off; corpus fractions should be read on that basis. The
submission-stage protocol requires two independent human coders plus adjudication and is
documented in `docs/HUMAN_VALIDATION_PROTOCOL.md`; its templates remain explicitly
`pending` until that work occurs. The downstream statistical analysis is separately
reproducible with fixed seeds via `make all`.
