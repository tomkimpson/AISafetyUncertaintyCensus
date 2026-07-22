# Second-Round Review of “Do Frontier-Safety Evaluations Have the Resolving Power Their Thresholds Imply?”

**Manuscript reviewed:** `paper/main.tex`
**Author response reviewed:** `PAPER_REVIEW.md`
**Review type:** Second-round methodological and publication-readiness review
**Recommendation:** Major revision

## Overall verdict

The paper is improved, especially in transparency, but I would not yet submit the current version to *Statistics and Public Policy*. The underlying contribution remains worthy of publication, but the headline “five of nine” result and the 83/98 census denominator are not methodologically secure enough to carry the paper in their present form.

Several revisions acknowledge the original objections without resolving their effect on the central quantitative claims. The manuscript is now more candid about its assumptions, but disclosure of an assumption is not by itself a validation of the result that depends on it.

The most defensible publishable core is:

- Published frontier-safety reports often omit quantified uncertainty and explicit statistical decision rules.
- The public record frequently does not permit an external reader to determine how uncertainty affected a governance conclusion.
- The Opus 4 uplift comparison is statistically unresolved under the conventional interpretations examined in the paper.
- Better reporting of sample sizes, uncertainty intervals, sampling units, and decision rules would materially improve auditability.

The least defensible parts remain the unconditional “five of nine” headline and the treatment of 83/98 as a stable census fraction.

## Improvements that are satisfactorily addressed

The following revisions represent genuine improvements:

1. **The estimand is now discussed explicitly.** The new paragraph names a task/trial-generalisation estimand and acknowledges the different case in which a rule is defined directly on a fixed benchmark.

2. **The incorrect TOST framing has been removed.** The manuscript now correctly describes the safety-relevant comparison as one-sided when the null is that capability meets or exceeds the danger threshold.

3. **The directional conventions are disclosed.** The manuscript now distinguishes its two-sided 95% Wilson resolve/straddle classification from its one-sided 95% power calculation and reports that the corresponding one-sided verdict changes the unresolved count from five to four.

4. **Several claims have been appropriately softened.** In particular, the manuscript now distinguishes an inability to verify a decision from a claim that the underlying decision was necessarily unreasonable.

5. **The uplift threshold is described more accurately.** The 2.8× figure is now presented as a supplementary threat-analysis heuristic rather than a binding RSP deployment threshold.

6. **A dedicated limitations section has been added.** It usefully consolidates the non-exhaustive corpus, AI-assisted extraction, single-developer auditable subset, SWE-bench reconstruction, clustering, and sample-size caveats.

7. **Presentation and reproducibility checks improved.** The PDF metadata is populated, the manuscript compiles, the numerical checks pass, and the repository language around the 2.8× heuristic is substantially better aligned with the manuscript.

These changes improve the honesty and readability of the paper. They do not, however, remove the major issues below.

## Remaining major issues

### 1. The “five of nine” headline is still model-dependent

Four of the nine audit rows are SWE-bench results reported as means over ten runs, not observed integer pass counts. The revision now says clearly that converting these means into task-level counts is a modelling choice rather than a property of the data. That is an important disclosure, but the abstract, conclusion, audit-table caption, and README still present the nine rows as one Bernoulli audit with an unconditional result of five unresolved thresholds.

The choice of sampling unit materially changes the result:

- Under the task-level reconstruction, 5/9 rows are unresolved.
- Under the run-level convention already reported in the manuscript, two SWE-bench verdicts change, leaving 3/9 unresolved.

A headline that changes from five to three solely because of an unresolved sampling-unit choice should not be reported simply as “five of nine.” The task-level analysis may be retained, but it should be presented as a conditional sensitivity analysis.

The cleanest presentation would split the result into tiers:

- Among the five direct count rows, 2/5 straddle their thresholds under the stated binomial working model.
- Among the four run-averaged SWE-bench rows, 3/4 straddle under the task-level convention, while 1/4 straddles under the run-level convention.
- Therefore, 5/9 is the result under one specified task-generalisation model, rather than an unconditional count directly observed in the published data.

This would preserve the SWE-bench evidence without asking it to support a stronger claim than the aggregates permit.

The generated audit-table caption also still describes all nine rows as reporting an integer pass count. That is inconsistent with the manuscript’s new acknowledgement that four counts are reconstructed from run-averaged scores.

### 2. The other five rows are not automatically “genuinely binomial”

The revised audit section describes the two bioweapons-knowledge rows and three METR rows as naturally binomial and says that the METR rows involve “each task scored once.” This is misleading.

The METR entries appear to involve repeated trials of a single task. A binomial model may be a reasonable working model if the trials are independent and identically configured, but that assumption must be stated. Repeated stochastic trials of one task are not the same sampling design as drawing independent tasks from a task population.

The 33 bioweapons questions are also a deliberately constructed benchmark rather than an identified random sample from a defined population of questions. A Wilson interval can be computed mechanically, but its superpopulation interpretation requires an additional assumption about what task population is being sampled and why these questions are representative of it. Human grading may introduce another source of variability not captured by the binomial calculation.

The paper should therefore replace language such as “genuinely binomial” or “sit naturally in a binomial model” with something conditional, for example:

> We analyse these rows under an IID Bernoulli working model. This treats the observed items or repeated trials as exchangeable draws from the target evaluation process; the public aggregates do not permit that assumption to be tested.

That wording would retain the analysis while being precise about what it establishes.

### 3. Naming the estimand does not establish the sampling population

The new estimand paragraph is helpful, but it asserts a population of tasks and trials without defining the relevant population or showing that the benchmark is a sample from it. SWE-bench hard tasks are deliberately selected, and the bioweapons questions are hand-constructed. Neither is an ordinary probability sample.

The paper should distinguish at least three inferential targets:

1. The empirical result on the fixed benchmark actually used by a framework.
2. Performance over stochastic reruns of that fixed benchmark under a specified evaluation configuration.
3. Performance over a broader superpopulation of possible tasks.

Only the second and third targets produce sampling uncertainty of the kind reconstructed in the paper, and each requires different data and assumptions. The manuscript may choose a superpopulation estimand, but it should describe the resulting intervals as conditional model-based generalisations, rather than implying that the benchmark design itself supplies random-sampling validity.

### 4. The census denominator remains unstable

The new caveat correctly says that the dataset is a best-effort structured compilation rather than a demonstrably exhaustive enumeration. It also acknowledges that some rows combine multiple models. Those admissions conflict with the stronger “census” framing and with the earlier statement that every row is one capability × model × card entry.

There are also apparent violations of the manuscript’s own governance-relevance inclusion criterion. For example:

- T7 is an HCAST benchmark row with no model, threshold, score, uncertainty, or apparent associated governance decision.
- A32 is explicitly labelled “NOT used for RSP” and “excluded from RSP call.”

If such rows remain in the denominator, 83/98 is a ratio of coding rows in a curated compilation rather than a well-defined prevalence estimate for governance-relevant evaluations.

This requires more than a limitation sentence. Before submission, the paper should:

1. Define a reproducible document sampling frame and cutoff.
2. State explicit inclusion and exclusion criteria.
3. Define a consistent row unit.
4. Recode or exclude entries that do not meet the governance-relevance definition.
5. Report how the headline fractions change under plausible alternative coding choices.

Renaming the dataset from a “census” to a “structured corpus” would reduce the overclaim, although the more important requirement is a defensible construction protocol. The number of textual replacements required is not a scientific reason to retain an inaccurate label.

### 5. The primary directional question and primary interval remain misaligned

The revision makes the inconsistency transparent but does not resolve it. The paper’s deployment argument is directional: for an upper danger threshold, the relevant null is that true capability is at or above the threshold. The headline classification instead uses a two-sided 95% interval, while the required-sample-size calculation uses one-sided 95% power.

These answer related but different questions. The choice affects the headline unresolved count: five under the two-sided 95% interval and four under the corresponding one-sided 95% analysis.

There are three defensible options:

1. Make the one-sided result primary because it matches the deployment question, reporting 4/9, with 5/9 as a two-sided sensitivity.
2. Define the primary research question as two-sided statistical discrimination and make the power calculation use the matching confidence convention.
3. Report both conventions equally prominently and avoid presenting either count as the unique answer.

Simply describing the two conventions as deliberately different does not explain why the larger, two-sided number should remain the paper’s headline while the conceptual argument is one-sided.

### 6. Several categorical claims still overstate the analysis

The abstract and discussion continue to suggest that every score-threshold comparison is inherently a statistical hypothesis test. That is not true when a framework defines a deterministic rule directly on a fixed benchmark. In that case the observed benchmark score can be compared with the rule without sampling inference; uncertainty becomes necessary when the score is interpreted as evidence about reruns, alternative tasks, or broader capability.

The discussion still says point-versus-threshold comparisons are “fundamentally” hypothesis tests, despite the new estimand paragraph acknowledging the fixed-benchmark exception. The conclusion also says that the record “uses the wrong statistical frame” and that the precautionary interpretation is “the only defensible reading.” Those claims go beyond what the audit establishes.

A more accurate central thesis would be:

> When a score is interpreted as evidence about performance beyond the particular observed benchmark or trials, quantified uncertainty and a stated decision rule are required to make the resulting governance inference externally auditable.

This remains a strong and useful argument without treating every numerical policy rule as a sampling-based hypothesis test.

### 7. Full human verification remains important for the corpus headline

The nine audited rows and uplift case have received manual verification, while the wider corpus has received an AI-assisted independent cross-check rather than equivalent row-by-row human sign-off. The manuscript now discloses this clearly, which is good practice.

Nevertheless, a headline such as 83/98 depends on every inclusion decision and coding field. A full human verification pass against the primary sources should be completed before submission if that fraction remains central. A limitation statement appropriately communicates residual risk, but it does not provide the same evidential assurance as source verification.

## Uplift case study

The uplift analysis is now substantially more defensible than the census and nine-row audit headlines. The manuscript properly distinguishes the 2.8× heuristic from a binding RSP threshold, and the qualitative conclusion is robust to the conventional interpretations of the reported “±13%” considered in the paper.

As an additional second-round check, unequal arm sizes were evaluated for all combinations with treatment and control sizes in {8, 9, 10}, using the current pooled-variance Fieller construction. All nine combinations still straddle 2.8. The qualitative conclusion is therefore not an artefact of assuming equal arm sizes.

Before submission, the analysis should still:

- explain the choice of degrees of freedom;
- add the unequal-arm calculation to the reproducible sensitivity analysis;
- consider or justify a Welch–Satterthwaite treatment if equal variances are not assumed; and
- describe the full disconnected Fieller confidence set when the denominator is insufficiently separated from zero.

These are important statistical refinements, but they do not presently threaten the qualitative uplift result.

Residual uses of “every admissible reading” should also be replaced with “the conventional readings considered here,” including occurrences in the appendix, analysis scripts, and generated captions. An unlabelled “±” quantity may have interpretations outside the three modelled cases.

## Technical and presentation checks

The following checks were completed during this review:

- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q`: **39 passed**.
- Hand-typed manuscript-number verification: **11/11 passed**.
- Pinned-source checksum verification: **all passed**.
- LaTeX compilation with `latexmk`: **successful**, producing a 19-page PDF.
- PDF title, author, subject, and keywords: **populated correctly**.

One nonfatal PDF warning remains:

```text
pdfTeX warning (dest): name{Hfootnote.1} has been referenced but does not exist
```

The appendix also remains visually dense, with some underfull/overfull box warnings. These are presentation issues rather than substantive blockers.

Some repository descriptions remain out of sync with the revised caveats. In particular, the README still calls the nine entries “machine-auditable Bernoulli rows,” and the generated audit caption still describes them as integer pass-count rows. Generated wording should be corrected at its source rather than editing generated files directly.

## Minimum revision path before submission

The smallest revision that would make the paper substantially more defensible is:

1. **Replace the unconditional 5/9 headline with a tiered result.** Report 2/5 for the direct-count working-model rows and report the four SWE-bench rows separately under both task- and run-level conventions.

2. **Describe every binomial calculation as conditional on an IID/exchangeability working model.** Correct the inaccurate description of the METR sampling unit.

3. **Formalise the corpus method.** Define the document sampling frame, inclusion rule, row unit, and recoding sensitivity; remove or justify entries that are not tied to governance decisions.

4. **Choose a primary directional convention.** Either make the one-sided result primary, match the two-sided power analysis, or headline both conventions.

5. **Narrow the thesis consistently.** Focus on external auditability of generalised capability claims rather than asserting that every fixed score-threshold comparison is intrinsically a hypothesis test.

6. **Complete human source verification for the corpus if 83/98 remains a headline statistic.**

7. **Finish the uplift-method details and repository wording cleanup.** These are secondary to the audit and corpus issues.

## Publication assessment and venue

The paper is worthy of publication in concept. Its reporting audit, reproducible source record, uplift case study, and proposal for explicit statistical decision rules make a potentially useful contribution. The present problem is not lack of an idea; it is that the manuscript asks its most assumption-sensitive reconstruction to support its most memorable quantitative claim.

After the revisions above, *Statistics and Public Policy* would be a plausible submission target. In the current version, a statistically attentive reviewer is likely to focus on the sampling-unit dependence of 5/9, the undefined superpopulation, and the unstable corpus denominator, and to recommend rejection or major revision despite agreeing with the broader motivation.

**Final recommendation: major revision before submission.**
