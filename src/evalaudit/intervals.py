"""Confidence intervals for a binomial proportion.

Thin, well-documented wrappers over ``statsmodels`` so the rest of the codebase
speaks one vocabulary. Wilson is the default (good small-sample coverage);
Clopper-Pearson ("beta") is the conservative exact interval.
"""

from __future__ import annotations

import numpy as np
from statsmodels.stats.proportion import proportion_confint

# Methods we expose; names match statsmodels' `method` argument.
CI_METHODS = ("wilson", "beta", "agresti_coull", "normal", "jeffreys")


def proportion_ci(successes, n, alpha=0.05, method="wilson"):
    """Two-sided ``(1 - alpha)`` confidence interval for a proportion.

    Parameters
    ----------
    successes : int
        Number of successful trials.
    n : int
        Total trials. Must be > 0.
    alpha : float
        Significance level; the interval has nominal coverage ``1 - alpha``.
    method : str
        One of :data:`CI_METHODS`. "beta" is Clopper-Pearson (exact).

    Returns
    -------
    (low, high) : tuple of float
    """
    if n <= 0:
        raise ValueError("n must be positive")
    if not (0 <= successes <= n):
        raise ValueError("successes must be in [0, n]")
    if method not in CI_METHODS:
        raise ValueError(f"method must be one of {CI_METHODS}, got {method!r}")
    low, high = proportion_confint(successes, n, alpha=alpha, method=method)
    # statsmodels can return values fractionally outside [0, 1] for the normal
    # method; clamp so downstream "straddles threshold" logic is well-behaved.
    return float(np.clip(low, 0.0, 1.0)), float(np.clip(high, 0.0, 1.0))


def proportion_directional_bounds(successes, n, alpha=0.05, method="wilson"):
    """Return the lower and upper one-sided ``(1 - alpha)`` bounds.

    The pair is computed as the endpoints of the central ``(1 - 2*alpha)``
    interval.  Each endpoint is therefore a one-sided ``(1 - alpha)`` bound;
    the pair is not a simultaneous ``(1 - alpha)`` interval.
    """
    if not (0.0 < alpha < 0.5):
        raise ValueError("alpha must be in (0, 0.5) for directional bounds")
    return proportion_ci(successes, n, alpha=2.0 * alpha, method=method)


def bootstrap_ci(successes, n, alpha=0.05, n_boot=20000, seed=0):
    """Percentile bootstrap CI for a proportion.

    Provided mainly as an independent cross-check on the closed-form intervals
    in robustness tables — not as the primary method.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    rng = np.random.default_rng(seed)
    p_hat = successes / n
    draws = rng.binomial(n, p_hat, size=n_boot) / n
    low = float(np.quantile(draws, alpha / 2))
    high = float(np.quantile(draws, 1 - alpha / 2))
    return low, high


def straddles(threshold, ci):
    """True if ``threshold`` lies inside or on the boundary of ``ci``.

    A straddling pair means that neither directional claim is demonstrated at
    the chosen one-sided confidence level.
    """
    low, high = ci
    return low <= threshold <= high
