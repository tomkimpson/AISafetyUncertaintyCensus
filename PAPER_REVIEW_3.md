# Third-Round Review of “Thresholds Without Error Bars: A Statistical Audit of Frontier AI Safety Evaluations”

**Manuscript reviewed:** `paper/main.tex`
**Prior reviews reviewed:** `PAPER_REVIEW.md`, `PAPER_REVIEW_2.md`
**Review type:** Third-round methodological, internal-consistency, and submission-readiness review
**Recommendation:** Major revision; not yet ready for submission to a statistically serious journal

## Bottom line

The paper has a strong, publishable core and an unusually good reproducibility package. The numerical
pipeline works, the sources for the central examples are archived, and the manuscript is much more
candid than the original version about modelling assumptions and the non-exhaustive corpus. The
Opus 4 uplift case continues to support a useful conclusion: the published summaries do not locate the
uplift ratio relative to 2.8× under the conventional interpretations examined.

The central quantitative claims are still not ready to carry the paper, however. In particular:

- “five of nine” remains the result of one selected sampling-unit convention, while the paper's own
  alternative convention gives three unresolved rows and its deployment-aligned one-sided convention
  gives four;
- the nine-row denominator is internally inconsistent with the paper's stated unit of analysis, most
  visibly because census row A4 contains two model results but the audit counts only Opus 4;
- the five non-SWE-bench rows are described inaccurately as singly scored items, although three are
  repeated runs of one task and the other two come from a deliberately constructed, manually graded
  question set; and
- the 98-row corpus still contains records that fail the manuscript's own governance-relevance rule and
  uses inconsistent row granularity.

These are not cosmetic caveats. They determine the numerators and denominators in the abstract and
conclusion. Reproducible computation from a chosen dataset does not establish that the dataset and
estimand identify the claimed scientific quantity.

My recommendation therefore remains **major revision**. If submitted in its current form, I would
expect a statistical referee to recommend reject-and-resubmit even while agreeing with the paper's
broader reporting critique.

## What is now strong

Several parts of the project can be treated as genuine strengths rather than continuing objections:

1. **The computational record is reproducible.** All 39 tests pass, the 11 manuscript-number guards
   pass, and the LaTeX source builds successfully into a 19-page PDF with populated metadata.

2. **The sources for the central audit are locally archived and traceable.** The Anthropic cards confirm
   the reported SWE-bench, METR-deduplication, bioweapons-knowledge, and uplift summaries used by
   the manuscript.

3. **The paper now acknowledges the key SWE-bench ambiguity.** The distinction between task- and
   run-generalisation is stated in the main text and marked in the generated table.

4. **The fixed-benchmark exception is acknowledged.** `main.tex:102` correctly concedes that a rule
   defined directly on a fixed benchmark can be checked without sampling inference.

5. **The uplift threshold is no longer presented as binding RSP policy.** The manuscript accurately
   identifies 2.8× and 5× as supplementary threat-analysis heuristics and notes that Anthropic escalated
   precautionarily.

6. **The limitations section is useful and candid.** It discloses non-exhaustiveness, AI-assisted corpus
   construction, single-developer auditability, and the main modelling assumptions.

The paper should be rebuilt around these strengths, particularly the externally auditable reporting
claim, rather than around a unique unresolved-count headline that the public aggregates do not identify.

## Major findings

### 1. “Five of nine” is still a conditional result presented as an unconditional finding

The abstract (`main.tex:78`), results (`main.tex:220-223`), and conclusion (`main.tex:388-391`) still
state that five of nine results cannot resolve their thresholds. Yet the generated audit table itself marks
two of those five with a dagger because they resolve below the threshold under the run-level convention
(`paper/tables/audit.tex:10-16,28-31`). The paper's own analyses therefore imply:

- **5/9** unresolved under the selected task-level, two-sided 95% Wilson convention;
- **3/9** unresolved under the run-level, two-sided 95% convention; and
- **4/9** unresolved under the one-sided 95% convention that matches the directional deployment
  question (`main.tex:210`).

Robustness to Wilson versus Agresti–Coull does not solve sensitivity to the observation model. The
former varies an interval formula while holding the constructed Bernoulli dataset fixed; the latter
changes what the observations actually are.

The minimum defensible presentation is tiered:

- report the five direct-count rows separately under an explicitly conditional IID/exchangeability
  working model;
- report the four SWE-bench rows under both task- and run-level conventions; and
- either make the deployment-aligned one-sided result primary or give the one- and two-sided results
  equal prominence.

The abstract should call 5/9 “the result under a task-generalisation, two-sided 95% working model,” not
the observed answer supplied by the published record.

### 2. The nine-row denominator is not internally coherent

The manuscript says each census result is a capability × model × card entry (`main.tex:121`), then
concedes that some rows bundle models (`main.tex:126-129`). The audit exposes a concrete consequence:

- Census row A4 contains **Opus 4 / Sonnet 4**, both reported at 17/33.
- The audit table includes only **Opus 4** for A4 (`paper/tables/audit.tex:17`).
- `data/raw/evals.csv:9` likewise contains only Opus 4, even though its source note explicitly says
  `Opus4=Sonnet4=17/33`.
- `main.tex:129` says the audit separates bundled models, but it does not separate this one.

If model-specific results are the unit, Sonnet 4 should be another audit entry and the denominator is
at least ten. If A4 is one shared row, the paper must stop describing the unit as model-specific and
must explain why identical values for two separately evaluated models count once while SWE-bench
model values count separately. The qualitative result changes little, but the memorable count changes
from 5/9 to 5/10.

This is not just a bookkeeping error. It demonstrates that “nine results” currently means “nine selected
coding rows,” not a stable set of evaluation results.

### 3. The five “direct” rows do not share the sampling design the text assigns to them

`main.tex:191-193` says the five non-SWE rows are “pass counts over singly-scored items” and that the
three METR rows involve “each task scored once.” The source cards say otherwise:

- METR data deduplication is **one task repeated for 29–46 trials**. Each trial is scored by whether its
  F1 exceeds 80%; it is not a set of independently sampled tasks.
- The 33 bioweapons questions are a deliberately constructed benchmark, manually graded by external
  experts. The Opus 4 card explicitly calls the score low-reliability/highly variable because of human
  grading.

A binomial calculation can still be presented as a working model, but it needs the correct conditional
interpretation. For the METR rows, it concerns stochastic reruns of one fixed task under a stable
configuration. For the bioweapons rows, a superpopulation interpretation requires treating the chosen
questions as exchangeable draws from a defined target population and ignoring grader variability.
Neither assumption follows from the public aggregate.

Replace “sit naturally in a binomial model” with wording such as:

> We analyse these rows under an IID Bernoulli working model. For METR this treats repeated runs of
> one fixed task as independent and identically configured; for bioweapons knowledge it treats the
> selected, manually graded questions as exchangeable items. The public summaries do not permit
> either assumption to be tested.

The paper should then distinguish fixed-benchmark performance, rerun performance on the same tasks,
and generalisation to new tasks throughout—not only for SWE-bench.

### 4. The 83/98 corpus headline is still not based on a stable construction protocol

The new caveat that 98 is a structured, non-exhaustive corpus is welcome, but the denominator still
violates the stated inclusion and unit rules.

Concrete examples include:

- T7 is an HCAST benchmark row with model=`benchmark`, no score, no threshold, no uncertainty, and
  no associated model decision.
- A32 explicitly says the evaluation was **not used for the RSP determination** and was “excluded from
  RSP call.”
- Opus 4 cyber subdomains are split into several rows, while the Claude 3.7 cyber subdomains are
  bundled into one.
- Some rows represent one model, some several models, some one metric, and some multiple metrics.
- The code classifies a sample size as reported whenever the `n` cell contains any digit. This counts
  entries such as “over 100 (buckets not reported)” even when the denominator corresponding to the
  displayed score is unavailable.

Consequently, 83/98 is a property of the current table layout, not an estimate attached to a normalized
evaluation-result unit. The conclusion that uncertainty reporting is uncommon is plausible and likely
robust, but its exact fraction is not yet scientifically interpretable.

Before submission, the paper needs:

1. a reproducible document sampling frame and search/cutoff protocol;
2. explicit inclusion and exclusion rules that are actually enforced;
3. one normalized row unit, with bundled records expanded or analyzed at a document level;
4. a distinction between “some sample count appears” and “the denominator for this score is reported”;
5. removal or justification of T7, A32, and comparable borderline rows; and
6. a recoding sensitivity table showing how the uncertainty fractions change.

Calling the dataset a **structured corpus** would fit what has actually been assembled. More
importantly, the exact 83/98 fraction should leave the abstract until the normalization is complete.

### 5. The primary decision question and primary interval remain mismatched

The discussion correctly formulates a directional safety claim as

\[
H_0: p \geq \tau, \qquad H_1: p < \tau.
\]

The primary verdict nevertheless uses a two-sided 95% interval, equivalent to a one-sided 97.5%
bound, while the power calculation uses a one-sided 5% test. Disclosure of the mismatch is not a
scientific justification for making the convention that yields the larger unresolved count the headline.

Choose one of three defensible presentations:

1. make the one-sided 95% result primary because it matches the governance claim;
2. define the scientific question as two-sided discrimination and use matching power calculations; or
3. present both symmetrically and avoid a unique unresolved-count headline.

The current combination makes the conceptual argument directional but the memorable number more
conservative than that argument requires.

### 6. The clustering robustness claim is false as written

`main.tex:230-232` says the two bioweapons verdicts “cannot be overturned by any possible
clustering” because doing so would require an ICC above 1. That conclusion holds only under the
assumed cluster size `m=5` in `scripts/run_audit.py:37-40`.

The reported critical design effect is 5.3. At `m=5`, the largest possible design effect is 5, so the
displayed ICC exceeds 1. But at `m=10`, the same critical design effect corresponds to

\[
\mathrm{ICC} = (5.3-1)/(10-1) \approx 0.48,
\]

which is entirely possible. Because the cluster definitions and sizes are unpublished, the manuscript
cannot infer impossibility from one assumed value of `m`. Replace “any possible clustering” with “the
illustrative `m=5` specification shown here,” and report sensitivity across the existing `m={5,10,20}`
grid.

The METR rows also should not be treated as automatically dependence-free merely because they use
one task. Item clustering is inapplicable, but repeated trials can still share prompts, scaffolds,
infrastructure, and other common conditions. Independence is a working assumption, not an observed
fact.

### 7. The paper still contradicts its own fixed-benchmark exception

The estimand paragraph correctly says that a deterministic rule on a fixed benchmark can be checked
without sampling uncertainty (`main.tex:102`). The abstract and discussion nevertheless say that a
score-threshold comparison is implicitly or “fundamentally” a hypothesis test (`main.tex:78,286-292`),
and the conclusion says the record uses “the wrong statistical frame” and that a precautionary reading
is “the only defensible” one (`main.tex:393-397`).

Those categorical claims are too broad. A framework can validly define a deterministic policy rule on
the observed benchmark. Statistical uncertainty becomes necessary when the observed result is used to
generalize to reruns, other tasks, latent capability, or future deployment performance.

A thesis that is both accurate and strong is:

> When an evaluation score is used as evidence about performance beyond the particular observed
> benchmark or trials, external auditability requires a stated estimand, quantified uncertainty, and a
> decision rule connecting that uncertainty to the governance action.

This is enough to motivate the paper without asserting that every numerical policy rule is inherently
a sampling-based hypothesis test.

### 8. The uplift conclusion is useful, but the confidence-set presentation remains incomplete

The qualitative uplift result is the strongest quantitative part of the paper: under each of the three
conventional interpretations examined, 2.8× remains inside the reconstructed set. The following details
should still be corrected:

- For the standard-error reading, the unconstrained Fieller set is disconnected. With the current
  rounded inputs and normal critical value it is approximately
  `(-∞, -131.2] ∪ [1.05, ∞)`, not simply `[1.05, ∞)`. Because both true arm means are nonnegative,
  intersecting with the nonnegative ratio parameter space can justify displaying only the positive ray,
  but that restriction must be stated.
- The SD calculation uses `t(df=n-1)` for two independent arms. The degrees of freedom need a pooled
  equal-variance or Welch–Satterthwaite derivation rather than an unexplained choice. This does not
  appear to change the straddle conclusion.
- The card says each arm contained 8–10 participants. The reproducible sensitivity analysis should
  include all unequal `(n_control,n_treatment)` combinations, not only equal 8, 9, and 10.
- Generated text still says “every admissible reading” (`paper/tables/uplift.tex:16-25` and
  `scripts/make_tables.py:125-134`). The main text's “three conventional readings we consider” is the
  accurate formulation.

These are method-reporting corrections, not reasons to discard the case study.

## Additional internal and presentation corrections

- `main.tex:137-139` first recognizes the Opus 4.7 and Gemini 3 Pro intervals, then says that apart
  from METR and DeepMind's 2024 paper all governance-relevant classifications use point estimates.
  The latter sentence contradicts the former and should be narrowed.
- The generated audit caption says all nine rows report integer pass counts
  (`paper/tables/audit.tex:22`), although four are reconstructed from run-averaged scores. Correct the
  generator, not the generated file.
- A `Beta(k+1,n-k+1)` distribution is the **Beta posterior under a binomial likelihood**, not a
  “Beta-Binomial posterior.” Beta-binomial normally names the marginal/predictive count distribution.
- The Wilson code treats a threshold exactly equal to a confidence-interval endpoint as resolved,
  whereas the manuscript says an interval containing the threshold is unresolved. This does not affect
  the current nine rows but should be made consistent.
- The README still uses the old paper title, says the manuscript “will be added,” and repeats the
  unconditional “nine Bernoulli rows / five unresolved” claim (`README.md:3-5,21`).
- The GPT-5.5 bibliography entry points to the marketing landing page even though the repository's own
  manifest says the evaluation content is on the Deployment Safety Hub
  (`references.bib:101-109`; `data/raw/sources/MANIFEST.md`).
- The GPT-5.6 bibliography entry gives July as the month, while the manuscript and manifest date the
  card to 25 June 2026 (`references.bib:111-118`).
- A clean LaTeX build still reports the unresolved `Hfootnote.1` destination. The landscape census is
  legible at high zoom but remains too dense for comfortable reading in print.

## Verification performed for this review

- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q`: **39 passed**.
- `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_paper_numbers.py`: **11/11 passed**.
- Clean `latexmk` build to a temporary output directory: **successful**, 19 pages.
- PDF title, author, subject, and keywords: **populated correctly**.
- Remaining PDF destination warning: `Hfootnote.1` unresolved.
- Primary Anthropic source pages for the nine audit rows and uplift case: spot-checked against the
  cached, hash-pinned PDFs.

These checks establish implementation consistency. They do not validate the sampling population,
row construction, or choice of primary decision convention.

## Minimum revision path

The smallest credible route to submission is:

1. **Remove the unconditional 5/9 claim from the abstract and conclusion.** Replace it with the tiered
   direct-count/SWE-bench results under explicitly named conventions.
2. **Normalize the audit denominator.** Decide whether A4 is one row or two model results, apply that
   rule throughout, and state the actual sampling design for each family.
3. **Normalize the corpus and rerun the counts.** Enforce the governance-relevance criterion, remove or
   justify T7/A32, distinguish score denominators from incidental sample counts, and report recoding
   sensitivity.
4. **Choose the primary directional convention.** Do not let the conceptual test and headline interval
   use different error rates without a substantive reason.
5. **Narrow the thesis to external auditability of generalized capability claims.** Preserve the
   fixed-benchmark exception consistently in the abstract, discussion, and conclusion.
6. **Correct the clustering and uplift set claims.** These are localized technical changes and do not
   require abandoning either analysis.
7. **Synchronize generated captions, README, bibliography, and PDF warnings.**

## Publication assessment

The project remains publishable in concept. Its most important contribution is not the exact fraction
5/9 or 83/98. It is the documented mismatch between the governance importance of frontier-safety
evaluations and the public record's frequent failure to state uncertainty, estimands, and decision rules.

That narrower contribution is well supported and valuable. The current manuscript weakens it by
placing assumption-sensitive reconstructed counts in the most prominent positions. A revision that
makes the corpus descriptive, the Bernoulli analyses explicitly conditional, and the reporting/auditability
argument primary would be substantially more persuasive.

**Final recommendation: major revision before submission.**

## Author implementation response (21 July 2026)

The revision implements the recommended major changes as follows.

1. **Corpus construction and coding.** `data/raw/census_records.csv` is now the canonical
   structured input. It assigns stable IDs, explicit eligibility, exclusion reasons,
   denominator status, and uncertainty class to all 98 screened records. T7 and A32 remain
   visible but are excluded from the 96-record primary corpus. The resulting primary counts
   are 73 score denominators, 8 partial/indirect sample reports, 15 with no sample count,
   9 proper intervals, 6 bare dispersions, and 81 with no uncertainty. A generated
   primary-versus-screened sensitivity table is included in the manuscript.

2. **Coherent audit unit.** The audit is now explicitly model-level. Shared record A4 maps
   to both Opus 4 and Sonnet 4, producing ten results while retaining the common source ID.
   The manuscript no longer presents one pooled unresolved fraction as an observed answer.

3. **Primary decision rule and tiers.** The deployment-aligned one-sided 95% Wilson bound is
   primary; central two-sided 95% intervals are a labelled sensitivity. Results are reported
   as 2/6 unresolved direct-count rows, 2/4 SWE rows under task generalisation, and 1/4 SWE
   rows under run generalisation. The two-sided sensitivity is 5/10 at task level and 3/10
   when SWE uses run-level denominators.

4. **Sampling-design language.** METR is described as repeated stochastic runs of one fixed
   task, the bioweapons set as deliberately constructed and manually graded, and SWE-bench
   under both task and task-run conventions. Every Bernoulli analysis is labelled an IID
   working model whose assumptions cannot be tested from the public aggregates.

5. **Clustering.** Critical design effects are translated across
   `m={5,10,20}`. The manuscript no longer infers impossibility from the illustrative
   `m=5` case and no longer equates inapplicable item clustering for METR with observed
   independence.

6. **Scope of the thesis.** The abstract, discussion, and conclusion now preserve the
   fixed-benchmark exception. The claim is limited to external auditability when a score is
   used to generalise beyond the observed benchmark or trials.

7. **Uplift reconstruction.** `FiellerResult` now preserves all confidence-set components.
   The standard-error reading reports the real-line set
   `(-inf,-131.18] U [1.05,inf)` and separately states the nonnegative-ratio restriction.
   All nine ordered control/treatment arm-size combinations are evaluated for the SD
   reading with Welch--Satterthwaite degrees of freedom. Generated text says “three
   conventional readings considered,” not “every admissible reading.”

8. **Internal consistency and presentation.** Equality with an interval endpoint is now
   unresolved; “Beta posterior” replaces “Beta-Binomial posterior”; the README, source-
   construction notes, reproducibility runbook, captions, figures, bibliography URLs/dates,
   and manuscript prose are synchronized. Removing the title footnote destination also
   eliminates the unresolved `Hfootnote.1` warning.

Verification after implementation: 40 unit tests pass; all 17 manuscript-number guards
pass; committed derived checksums pass; all 26 manifest sources resolve and all 10
manifest-pinned hashes match; and a clean `latexmk` build succeeds at 19 pages with populated
PDF metadata and no undefined references or unresolved destinations.

One submission gate is intentionally still open. `data/verification/human_signoff.csv`
lists all 96 eligible records with `human_status=pending`. The manuscript explicitly
discloses this status and must not be represented as having completed row-by-row human
verification until the author supplies the signer, date, and disposition for every record.
