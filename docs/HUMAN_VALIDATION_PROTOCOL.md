# Independent human validation protocol

## Purpose and submission rule

The corpus extraction and current claim-fidelity pass were AI-assisted. They are
useful for analysis development but are not a substitute for independent human
verification. Before journal submission, two human coders must independently
recode every screened census record and every model-level threshold
reconstruction from the pinned source documents. A third person, or the two
coders jointly with an explicit record, must adjudicate all disagreements.

`make verify-human` is the submission gate. It is intentionally failing while
any row is marked `pending`. Do not describe the study as human-validated until
that command passes and the resulting coding has been reconciled with the
canonical inputs.

## Materials

- Source frame and locators: `data/raw/sources/MANIFEST.md`
- Coding definitions: `data/raw/sources/CONSTRUCTION.md`
- Independent census template: `data/verification/human_validation.csv`
- Census adjudication: `data/verification/human_adjudication.csv`
- Independent model-audit template:
  `data/verification/model_audit_validation.csv`
- Model-audit adjudication:
  `data/verification/model_audit_adjudication.csv`

Regenerate missing blank templates with:

```sh
python scripts/seed_human_validation.py
```

The script preserves existing files by default. `--force` erases entered human
coding and should only be used deliberately.

## Independence and blinding

1. Assign `HUMAN_A` and `HUMAN_B` to people who did not perform the original
   AI-assisted extraction.
2. Give each coder a separate copy of the templates. Do not let either see the
   other coder's entries before both copies are frozen.
3. Ask coders to work from the source documents and coding manual, not from the
   existing values in `census_records.csv`, `evals.csv`, paper tables, or
   headline aggregate counts.
4. Record `source_checked=yes` only after opening the pinned document and
   locating the cited result. Use `notes` or `mapping_notes` for ambiguous or
   inaccessible material.
5. Preserve each frozen independent file before merging it into the repository.

Complete blinding to row identity is impossible because the template carries
stable IDs and source locators. The practical goal is independent judgment, not
concealment of the source.

## Census coding rules

Code all 98 screened records, including the two currently excluded rows.

- `include_primary`: `true` only for a source-reported evaluated-model result
  mapped to a safety-relevant capability or deployment determination.
- `n_status`:
  - `score_denominator`: a count tied to the displayed score;
  - `partial_or_indirect`: numerical sample information that does not identify
    that score denominator;
  - `not_reported`: neither is available.
- `uncertainty_class`:
  - `proper_interval`: inferential construction plus stated coverage or
    credibility level;
  - `bare_dispersion`: an uncertainty or variability quantity without an
    identified interval construction and level;
  - `none`: no uncertainty quantity for the result.

Do not infer an interval from a bare `±`, infer a denominator from unrelated
counts, split bundled source rows, or treat multiple records from one document
as independent observations.

## Model-level threshold reconstruction

For each of the ten model-level rows, independently record:

- the score as displayed by the source;
- the denominator used by the reconstruction;
- the corresponding integer success count, if a binomial reconstruction is
  defensible;
- the operative numerical threshold and its direction; and
- any judgment needed to map source prose to the comparison.

The human task is source reconstruction, not recomputation of Wilson bounds.
After adjudication, run the analysis pipeline and compare its three-way classes
with the paper.

## Adjudication and analysis

After both independent files are frozen:

1. Compare each field without replacing either coder's entry.
2. Resolve every disagreement against the pinned source and record the final
   value, adjudicator, and rationale in the adjudication files.
3. Mark a row `complete` only when all required fields are filled.
4. Run `make verify-human`. Report raw agreement and Cohen's kappa for the three
   categorical census fields. Because kappa is prevalence-sensitive, always
   report raw agreement and the category marginals alongside it.
5. Diff adjudicated values against the current canonical inputs. Update the
   canonical CSVs only through a reviewed change, regenerate all derived data,
   and rerun tests and manuscript number checks.

The purposive source frame does not support a sampling-based confidence
interval around the 81/96 descriptive fraction. Human coding reliability and
source/document weighting sensitivities address different—and relevant—forms
of uncertainty.
