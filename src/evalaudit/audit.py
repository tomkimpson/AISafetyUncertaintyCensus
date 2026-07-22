"""Single entry point: does this eval resolve its own threshold?

    from evalaudit import audit
    r = audit(score=0.42, n=100, threshold=0.50)
    print(r.verdict)          # e.g. "CANNOT RESOLVE"
    print(r.directional_bounds)  # one-sided 95% lower/upper bounds
    print(r.prob_above)       # posterior P(capability > threshold)
    print(r.required_n)       # trials needed to resolve the observed gap

Feed it the numbers a deployment decision rested on; it returns whether those
numbers can actually place the model on one side of the framework's threshold.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Optional

from .intervals import proportion_ci, proportion_directional_bounds, straddles
from .bayes import prob_above, credible_interval
from .power import power_vs_threshold, required_n
from .clustered import cluster_robust_se, effective_n


@dataclass
class AuditResult:
    # inputs
    n: int
    successes: int
    score: float
    threshold: float
    direction: str
    alpha: float
    # frequentist: the directional bounds are primary; the central interval is
    # retained as a pre-specified sensitivity analysis.
    directional_bounds: tuple
    two_sided_ci: tuple
    ci_method: str
    unresolved_directional: bool
    unresolved_two_sided: bool
    # effective sample size after clustering (falls back to n)
    effective_n: float
    # power / sizing
    power_at_observed: float
    required_n: Optional[int]
    # bayesian
    prob_above: float
    credible_interval: tuple
    # summary
    verdict: str
    notes: list = field(default_factory=list)

    def as_dict(self):
        return asdict(self)

    @property
    def ci(self):
        """Backward-compatible alias for the primary directional bounds."""
        return self.directional_bounds

    @property
    def straddles_threshold(self):
        """Backward-compatible alias for the primary unresolved indicator."""
        return self.unresolved_directional


def _resolve_counts(successes, n, score):
    if successes is None and score is None:
        raise ValueError("supply either successes or score")
    if successes is None:
        successes = int(round(score * n))
    successes = int(successes)
    if not (0 <= successes <= n):
        raise ValueError("successes must be in [0, n]")
    return successes, successes / n


def audit(
    n,
    threshold,
    successes=None,
    score=None,
    alpha=0.05,
    direction="above",
    ci_method="wilson",
    prior=(1.0, 1.0),
    target_power=0.95,
    cluster=None,
):
    """Audit whether an eval result resolves its governance threshold.

    Parameters
    ----------
    n : int
        Number of eval items (nominal sample size).
    threshold : float
        The framework's capability threshold (a proportion in [0, 1]).
    successes, score : int or float
        Provide exactly one: raw successes, or the reported accuracy/score.
    alpha : float
        Significance level for the primary one-sided test. The reported lower
        and upper bounds each have coverage ``1 - alpha``. A central
        ``1 - alpha`` interval is also returned as a sensitivity analysis.
    direction : {"above", "below"}
        "above": danger means exceeding the threshold (the usual case).
        "below": the threshold is a floor the model must clear.
    ci_method : str
        Passed to :func:`evalaudit.intervals.proportion_ci`.
    prior : tuple
        Beta prior for the Bayesian mirror.
    target_power : float
        Power used for the required-N back-calculation.
    cluster : tuple or None
        Optional ``(cluster_successes, cluster_sizes)`` to compute a
        cluster-robust effective n. When given, the reported point estimate is
        taken from the clustered decomposition.

    Returns
    -------
    AuditResult
    """
    notes = []

    if cluster is not None:
        c_succ, c_size = cluster
        p_hat, se_c = cluster_robust_se(c_succ, c_size)
        n_eff = effective_n(n, se_clustered=se_c, p_hat=p_hat)
        successes = int(round(p_hat * n))
        score = p_hat
        notes.append(
            f"clustered: cluster-robust SE={se_c:.4f} implies effective n≈{n_eff:.0f} "
            f"(nominal {n})"
        )
    else:
        n_eff = float(n)

    successes, score = _resolve_counts(successes, n, score)

    directional_bounds = proportion_directional_bounds(
        successes, n, alpha=alpha, method=ci_method
    )
    two_sided_ci = proportion_ci(successes, n, alpha=alpha, method=ci_method)
    unresolved_directional = straddles(threshold, directional_bounds)
    unresolved_two_sided = straddles(threshold, two_sided_ci)

    # Power of the deployment test if the truth equals the observed score.
    power_obs = power_vs_threshold(n, threshold, score, alpha, direction, "normal")

    # How many trials to resolve the *observed* gap at target power?
    req_n = None
    if score != threshold:
        req_n = required_n(threshold, score, alpha, target_power, direction)

    p_above = prob_above(threshold, successes, n, prior)
    cred = credible_interval(successes, n, alpha=alpha, prior=prior)

    # Verdict.
    if unresolved_directional:
        verdict = "CANNOT RESOLVE"
        notes.append(
            f"the one-sided {int((1-alpha)*100)}% directional bounds "
            f"{directional_bounds[0]:.3f}–{directional_bounds[1]:.3f} contain the "
            f"threshold {threshold:.3f}: the eval does not distinguish safe from "
            f"dangerous at this confidence."
        )
    else:
        side = "above" if score > threshold else "below"
        verdict = f"RESOLVED ({side} threshold)"
    notes.append(
        f"posterior P(capability {'>' if direction=='above' else '<'} threshold) = "
        f"{(p_above if direction=='above' else 1-p_above):.3f}"
    )
    if req_n is not None and req_n > n:
        notes.append(
            f"to resolve the observed {abs(score-threshold):.3f} gap at "
            f"{int(target_power*100)}% power would need n≈{req_n} "
            f"({req_n/n:.1f}× the reported {n})."
        )

    return AuditResult(
        n=int(n),
        successes=successes,
        score=score,
        threshold=threshold,
        direction=direction,
        alpha=alpha,
        directional_bounds=directional_bounds,
        two_sided_ci=two_sided_ci,
        ci_method=ci_method,
        unresolved_directional=unresolved_directional,
        unresolved_two_sided=unresolved_two_sided,
        effective_n=n_eff,
        power_at_observed=power_obs,
        required_n=req_n,
        prob_above=(p_above if direction == "above" else 1 - p_above),
        credible_interval=cred,
        verdict=verdict,
        notes=notes,
    )
