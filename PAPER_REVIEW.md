# Objective pre-submission review

## Bottom line

This manuscript contains a publishable contribution, but I would not submit the present version. My referee recommendation would be **major revision**—possibly reject-and-resubmit at a statistically serious journal.

The useful contribution is the documented reporting audit: frontier-safety evaluations often omit uncertainty and explicit decision rules. The repository is unusually reproducible, the code passes all 39 tests, and the numerical outputs agree with the manuscript. But the stronger “five of nine cannot resolve their threshold” result currently relies on an inadequately justified sampling model. That is central enough that a competent statistical reviewer is likely to challenge the paper’s headline rather than merely request clarification.

In short: this is a worthy research question and potentially a worthy paper, but it is not yet defensible in its current statistical framing.

## Major issues to fix

### 1. The estimand and sampling population are not defined

The paper assumes that comparing an evaluation score with a threshold is necessarily a hypothesis test about a latent “true capability.” It is only such a test after defining what randomness and population the inference concerns:

- repeated stochastic runs on these exact tasks;
- unseen tasks sampled from some target population;
- different prompts or scaffolds;
- human graders or participants; or
- the model’s performance on a fixed benchmark.

Some frameworks may define their rule directly on an observed fixed benchmark. In that case, no sampling uncertainty is required to determine whether the empirical rule was crossed, although external validity remains uncertain.

This distinction must be introduced near the opening claim in `paper/main.tex`, not deferred to an appendix.

### 2. The four SWE-bench rows are not straightforward Bernoulli counts

Three scores are explicitly fractional averages over repeated runs: 16.6/42, 15.4/42, and 9.65/42. The threshold itself is defined as performance averaged over 10 runs. Nevertheless, the analysis rounds each score into an integer number of successes over 42 tasks and applies a binomial Wilson interval.

That changes the estimand from Anthropic’s fixed-task, repeated-run criterion to generalisation over a hypothetical population of tasks. The latter may be worth studying, but it is the paper’s chosen estimand, not necessarily the framework’s decision rule. Opus 4.5’s integer-looking 21/45 is still reported under a 10-trial averaging rule, so its observation model is also unclear.

Consequently, calling all nine rows “integer pass counts over Bernoulli trials” is not currently supportable. If all four SWE rows were excluded, the displayed audit would contain five rows, two of which straddle under the present calculation. That illustrates how much the headline depends on this choice.

Either obtain run/task-level data and fit an appropriate hierarchical or task-by-run model, or remove these rows from the binomial headline and present them as a separate sensitivity analysis.

### 3. The census denominator is not a stable unit of analysis

The manuscript says each row is one capability × model × card result, but the table sometimes combines models and sometimes separates them. For example, A4 combines Opus 4 and Sonnet 4 in one row, while the uplift results separate them. DeepMind rows similarly combine several models. Some included rows have no score or threshold, while A32 explicitly concerns an evaluation not used for the RSP decision.

Therefore, “83 of 98” describes coding rows, not a well-defined population of evaluation results. This does not invalidate the observation that uncertainty reporting is uncommon, but it prevents interpreting 83/98 as a meaningful prevalence estimate.

Add a genuine corpus-methods section covering:

- the complete document universe and search cutoff;
- source selection and exclusion rules;
- a normalized unit of analysis;
- treatment of multiple models, domains, variants, and repeated cards;
- duplicate results;
- a flow diagram or source inventory; and
- sensitivity of the counts to reasonable recoding.

Unless exhaustiveness can be demonstrated, call it a “structured audit” or “corpus,” not a census.

### 4. The directional tests are inconsistent

A two-sided 95% interval amounts to a 97.5% one-sided bound, but the power calculation uses a one-sided 5% test. For the directional claim “performance is below the safety threshold,” the natural procedure is a one-sided upper confidence bound with a predeclared error rate. The paper’s own 90% two-sided sensitivity—which corresponds to a 95% one-sided bound—reduces the unresolved count from five to four.

Choose and justify one decision rule, then use it consistently for intervals, power, and Bayesian posterior cutoffs.

The discussion of TOST is also incorrect. Demonstrating that a parameter lies below one upper threshold is a one-sided noninferiority/superiority-style test with null hypothesis \(p \geq \tau\), not an equivalence test requiring two one-sided tests. Remove the TOST argument unless both lower and upper equivalence margins are introduced.

### 5. Several claims overstate what the evidence establishes

Examples include:

- “A CI or error bar with no threshold … cannot inform the decision.” It can inform qualitative judgment, model comparison, or trend assessment.
- “This provides false reassurance.” At most, it *can be read* as reassurance; the cards often use holistic decision processes.
- “The governance decisions … were reasonable.” The paper does not evaluate their overall reasonableness.
- “The published record cannot underwrite that claim.” Absence of a published interval means outsiders cannot verify the inference, not necessarily that the underlying evidence could not support it.

The paper will be more credible if its central conclusion is narrower:

> The public reporting is insufficient to reconstruct or verify a consistent uncertainty-aware decision rule.

That claim is strong and well supported.

### 6. The uplift case is useful but explicitly conditional

Its qualitative conclusion probably survives, but change “every admissible reading” to “three plausible conventional interpretations.” An unlabelled ± value could have other origins. Also:

- consider unequal 8–10 participant arm sizes, not only equal-sized arms;
- justify the degrees of freedom, ideally with a Welch–Satterthwaite calculation;
- describe the full disconnected Fieller confidence set under an imprecise denominator; and
- consistently identify the 2.8× and 5× figures as threat-analysis/rule-out heuristics rather than binding RSP policy.

Anthropic escalated despite the 2.53× point estimate. That makes this a good example of inadequate public statistical documentation, but not an example of an unsafe decision caused by ignoring uncertainty.

### 7. Human verification should be stronger

The nine audited rows were manually checked, but the remaining census was AI-assisted both in extraction and verification. Because 83/98 is a headline empirical result, every included row should be manually verified before journal submission and that sign-off should be recorded. The current disclosure is appropriately explicit, but a reviewer may reasonably question an AI-generated and AI-cross-checked dataset.

Repository language that still calls the 2.8× line “binding” or “central” should also be updated so that it agrees with the manuscript’s more accurate qualification.

## Presentation issues

The manuscript is readable and the title is effective, although slightly prosecutorial. The 19-page PDF compiles, but has one unresolved hyperlink/footnote warning, numerous cramped appendix cells, and empty PDF metadata.

There are also a few copy-editing errors:

- “Stelling et al. assesses” → “assess”
- “Tong et al. publishes” → “publish”
- “Bommasani et al. evaluates” → “evaluate”
- “the most transparent absorbs” → “the most transparent absorb”

Add a dedicated limitations section. At present, important limitations are scattered through the audit and appendix, which makes the headline appear more settled than it is.

## Journal recommendation

The first choice after major revision should be **[Statistics and Public Policy](https://www.tandfonline.com/action/journalInformation?journalCode=uspp20&show=aimsScope)**. It is an American Statistical Association journal specifically seeking sound statistical thinking applied to public-policy questions, and it explicitly says that novel statistical methodology is not required when existing techniques are applied insightfully. That matches this paper unusually well. It is fully open access, so the applicable publication charge or University of Melbourne publishing agreement should be checked before submission.

A realistic interdisciplinary fallback is the **[Journal of Responsible Technology](https://www.sciencedirect.com/journal/journal-of-responsible-technology)**. Its scope explicitly includes technology policy and governance, practical applications, and varied methodologies. It is also gold open access and currently lists a USD 1,850 article publishing charge.

I would not lead with *AI and Ethics* unless the manuscript adds a substantive normative ethics argument. Its [current scope](https://link.springer.com/journal/43681/aims-and-scope) says that descriptive or empirical governance work without explicit ethical analysis is out of scope.

## Recommended submission strategy

Revise the estimand, remove or remodel the SWE-bench rows, normalize the corpus, and then submit to *Statistics and Public Policy*.

The paper’s strongest defensible contribution is not:

> Five evaluations statistically failed.

It is:

> Public frontier-evaluation reporting generally does not permit an independent, uncertainty-aware conformity assessment.

That is a worthwhile and publishable result.

---

# Response — actions taken (author-side revision pass)

This section records what was changed in response to the review, and where I agree or
disagree with each point. All edits in this pass are **text and comments only**: no computed
number, table value, figure, or the "5 of 9" headline was altered. `src/`, `paper/tables/`,
and all derived CSVs are unchanged, and the 39-test suite still passes. Work was done on the
`paper-review-fixes` branch.

Legend: **Done** (implemented), **Partial** (substance addressed by a lighter change than
proposed), **Deferred** (agree in principle, but out of scope for a text pass), **Disagree**.

## Major issues

**1. Estimand / sampling population not defined — Partial (agree).**
Added a dedicated estimand paragraph to the Introduction (`main.tex`, after the framing
question) naming the estimand explicitly: the model's *true pass rate over the population of
tasks/trials* from which the reported evaluation is a finite sample, and stating that the
randomness is task/run sampling, not prompt/scaffold/grader variation (which the aggregates
can't separate). It also concedes the "rule defined directly on a fixed benchmark" case the
review raises. This surfaces content that previously lived only in Appendix B (`task-generalisation`)
into the opening, as requested.

**2. SWE-bench rows are not straightforward Bernoulli counts — Partial (agree with the
critique; disagree with removal). My judgement call.**
I kept the four SWE-bench rows and the "5 of 9" headline, but stopped the main text from
describing all nine as clean "integer pass counts." The audit-section intro now distinguishes
the five genuinely-binomial rows (two bioweapons + three single-run METR) from the four
SWE-bench rows, states plainly that treating a ten-run *mean* as an integer count is a
*modelling choice, not a property of the data*, and tells the reader who rejects that choice
to read the four SWE rows as the Appendix-B sensitivity analysis rather than part of the
headline. *Why not remove them or fit a hierarchical model:* the run/task-level data is
unpublished, so a hierarchical fit is impossible from the public record; and the paper already
defends the task-generalisation estimand and reports the ±1-count and run-generalisation
sensitivities (App. B). Removing the rows outright would be *less* transparent than keeping
them with an explicit, prominent caveat and an escape hatch to the sensitivity tier.
**Deferred:** obtaining run/task-level data + hierarchical refit.

**3. Census denominator / "census" not a stable unit — Partial (agree with the critique;
disagree with the rename). My judgement call.**
I kept the term "census" but added a two-caveat note to §Census: (i) it is a best-effort
structured compilation to a June 2026 cutoff, *not* a proven-exhaustive enumeration, so its
fractions are prevalence-within-corpus, not a population estimate; (ii) the unit is not always
one model — some rows follow the source in bundling models (e.g. Opus 4 / Sonnet 4) even
though the audit separates them. *Why not rename to "corpus" / add a full corpus-methods
section + flow diagram:* renaming touches 42 usages plus the paper's central framing and, in
my judgement, is disproportionate to the actual defect, which is an honesty caveat the term
can carry. The substantive gap (what is counted, and that multi-model rows exist) is closed by
the caveat. **Deferred:** a full PRISMA-style flow diagram / recoding-sensitivity table.

**4. Directional tests inconsistent + TOST is wrong — Done (agree).**
Two edits. (a) *TOST:* the review is technically correct — demonstrating the true value lies
below a *single* upper line is a one-sided noninferiority/superiority test with H₀: p ≥ τ, not
a two-one-sided-tests equivalence procedure. I rewrote the Discussion ¶3 passage to state the
one-sided framing (danger is the null; burden reverses) and removed the TOST machinery and the
`schuirmann1987` citation (kept `lakens2017`/`wellek2010` as noninferiority references). (b)
*Directional consistency:* rather than re-running the analysis one-sided (which would move
numbers), I added a sentence in §Audit that deliberately distinguishes the two conventions —
a conservative two-sided 95% Wilson interval for the resolve/straddle verdict vs. a one-sided
95% power formula for the directional `n_req` — and notes the two-sided-90% = one-sided-95%
correspondence already tabulated in App. B (5 → 4).

**5. Several claims overstate the evidence — Done (agree).**
- "A CI/error bar with no threshold … cannot inform the decision" → now concedes it *can*
  inform qualitative judgment, comparison, and trend, but not the *point-versus-threshold*
  decision.
- "This provides false reassurance" → "This can be read as false reassurance."
- "The published record cannot underwrite that claim" → reframed as *does not let an outside
  party verify that claim, whatever the merits of the underlying evidence* — i.e. the paper's
  own narrower, better-supported thesis.
- Conclusion "The governance decisions … were reasonable" → "may well have been reasonable
  … appear precautionary," matching the abstract's existing hedge (this was also an internal
  inconsistency).

**6. Uplift case is conditional — Partial (agree on wording; deferred on extra stats).**
Softened "any/each admissible reading" → "any of the three conventional readings we consider"
in the Conclusion and Fig. 2 caption, conceding an unlabelled ± could have other origins. The
2.8×/5× figures are already framed as supplementary threat-analysis heuristics, "never binding
policy" (§Uplift); repo prose was reconciled to match (see item 7). **Deferred:** unequal
8-vs-10 arm sizes, a Welch–Satterthwaite dof justification, and the full disconnected Fieller
set under an imprecise denominator — these are code changes; the paper already covers n = 8,9,10
equal arms and the unbounded-SE reading.

**7. Human verification / repo language — Partial.**
*Repo language (Done):* reconciled "binding"/"central" wording for the 2.8× line with the
manuscript's qualification across `scripts/uplift_analysis.py`, `scripts/make_uplift_figure.py`,
`data/raw/census_full.md`, and `README.md`. (Left `docs/REPRODUCIBILITY.md:69` "central claims"
as-is: there "central" correctly means the headline claims carried by the Tier-0 verification
rows, not the 2.8× line.) *Manual verification (Deferred):* full row-by-row human sign-off of
all 98 census rows is research labor against the primary sources, not a text edit. I added it
explicitly to the new Limitations section as a stated caveat a reader should weigh.

## Presentation

- **Copy-edits — Done.** Fixed all four subject-verb errors (`assess`, `publish`, `evaluate`,
  `absorb`) plus a fifth identical case the review missed (`fli2025index … publish`).
- **PDF metadata — Done.** Filled `pdftitle`/`pdfauthor`/`pdfsubject`/`pdfkeywords` into the
  active `\hypersetup` and removed the commented placeholder block. (Not compiled — author
  compiles LaTeX; run `pdfinfo paper/main.pdf` after recompiling to confirm.)
- **Limitations section — Done.** Added a dedicated `\section{Limitations}` between Discussion
  and Conclusion consolidating the previously-scattered caveats (corpus non-exhaustiveness,
  AI-assisted extraction, single-developer audit, SWE-bench/DEFF/± modelling choices, `n_req`
  as order-of-magnitude).
- **Cramped appendix cells / hyperlink warning — Deferred.** Cosmetic LaTeX issues best judged
  against a fresh compile by the author.

## Journal recommendation & strategy

No action — these are editorial recommendations, not manuscript defects. Noted for the author.
