"""Scaled-Beta arm models and a parametric bootstrap for a ratio of means.

The Opus 4 bio-uplift arms are means of a continuous rubric bounded on [0, 100].
A Normal arm model is a poor fit at the boundary: at the 25% control mean a
Normal with the SD implied by the "±13% is an SE" reading places substantial
mass below zero. A Beta distribution scaled to [0, support] is the natural
bounded alternative, and matching its mean and SD lets us (a) bootstrap the
ratio-of-means interval without assuming Normality and (b) test whether a
claimed dispersion is even attainable on a bounded score (Bhatia--Davis).

This module is shared by ``scripts/uplift_analysis.py`` (point-estimate
intervals) and ``scripts/coverage_sim.py`` (interval coverage simulation) so the
matching logic is defined once and unit-tested.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def bhatia_davis_max_sd(mean, support=100.0):
    """Largest SD attainable by any distribution on ``[0, support]`` with this
    mean (Bhatia--Davis inequality): ``sqrt(mean * (support - mean))``."""
    if not (0 <= mean <= support):
        raise ValueError("mean must lie in [0, support]")
    return float(np.sqrt(mean * (support - mean)))


@dataclass
class BetaMatch:
    """A Beta(a, b) on [0, support] matched to a target mean and SD.

    ``feasible`` is False when the requested SD exceeds the Bhatia--Davis bound
    for the mean, in which case ``a``/``b`` are NaN: no distribution on the
    bounded support (Beta or otherwise) can have that mean and that SD.
    """

    a: float
    b: float
    support: float
    mean: float
    sd: float
    feasible: bool


def match_scaled_beta(mean, sd, support=100.0):
    """Match a scaled Beta on ``[0, support]`` to ``mean`` and ``sd``.

    With ``x = mean/support`` and ``s = sd/support``, a Beta(a, b) has
    ``var = x(1-x)/(a+b+1)``, so ``a+b+1 = x(1-x)/s^2``. Returns a
    :class:`BetaMatch`; ``feasible=False`` if ``s^2 >= x(1-x)`` (the scaled
    Bhatia--Davis / Beta-variance ceiling)."""
    if support <= 0:
        raise ValueError("support must be positive")
    x = mean / support
    s = sd / support
    if not (0 < x < 1):
        return BetaMatch(float("nan"), float("nan"), support, mean, sd, False)
    max_var = x * (1 - x)
    if s * s >= max_var or s <= 0:
        return BetaMatch(float("nan"), float("nan"), support, mean, sd, False)
    nu = max_var / (s * s) - 1.0  # = a + b
    a = x * nu
    b = (1 - x) * nu
    return BetaMatch(float(a), float(b), support, mean, sd, True)


def sample_arm(rng, match: BetaMatch, n):
    """Draw ``n`` participant scores from a matched scaled-Beta arm."""
    if not match.feasible:
        raise ValueError("cannot sample an infeasible Beta match")
    return match.support * rng.beta(match.a, match.b, size=n)


def bootstrap_ratio_ci(
    m1, sd1, n1, m0, sd0, n0, support=100.0, alpha=0.05, n_boot=20000, seed=0
):
    """Percentile-bootstrap CI for the ratio of means ``m1 / m0``.

    Resamples each arm from a scaled-Beta matched to its (mean, SD) at the arm's
    n, recomputes the ratio of sample means, and returns
    ``(ratio, low, high, feasible)``. ``feasible`` is False (and the interval is
    NaN) when either arm's SD is infeasible on the bounded support.
    """
    match1 = match_scaled_beta(m1, sd1, support)
    match0 = match_scaled_beta(m0, sd0, support)
    r = float(m1 / m0)
    if not (match1.feasible and match0.feasible):
        return r, float("nan"), float("nan"), False
    rng = np.random.default_rng(seed)
    a1 = support * rng.beta(match1.a, match1.b, size=(n_boot, n1))
    a0 = support * rng.beta(match0.a, match0.b, size=(n_boot, n0))
    ratios = a1.mean(axis=1) / a0.mean(axis=1)
    lo = float(np.quantile(ratios, alpha / 2))
    hi = float(np.quantile(ratios, 1 - alpha / 2))
    return r, lo, hi, True
