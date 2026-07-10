"""Power, minimum detectable effect, and required sample size.

The governance question is a one-sample test of a proportion against a *fixed*
threshold ``p0`` (the framework's capability threshold), not a two-sample
comparison. We model the deployment test as one-sided:

    H0: p = p0        (model sits exactly at the threshold)
    H1: p > p0        direction="above"  (danger = exceeding the threshold)
        p < p0        direction="below"  (danger = the eval is a floor to clear)

Both a normal approximation and an exact-binomial method are provided; the
normal formulas give the familiar closed forms, the exact method is the
robustness check for small ``n``.
"""

from __future__ import annotations

import numpy as np
from scipy import stats


def _z(alpha):
    return stats.norm.ppf(1.0 - alpha)


def power_vs_threshold(n, p0, p1, alpha=0.05, direction="above", method="normal"):
    """Power to detect a true rate ``p1`` against threshold ``p0``.

    Returns the probability that a one-sided level-``alpha`` test rejects
    ``H0: p = p0`` when the truth is ``p1``.
    """
    if direction not in ("above", "below"):
        raise ValueError("direction must be 'above' or 'below'")
    n = int(n)
    if n <= 0:
        raise ValueError("n must be positive")

    if method == "normal":
        za = _z(alpha)
        if direction == "above":
            crit = p0 + za * np.sqrt(p0 * (1 - p0) / n)
            return float(stats.norm.cdf((p1 - crit) / np.sqrt(p1 * (1 - p1) / n)))
        crit = p0 - za * np.sqrt(p0 * (1 - p0) / n)
        return float(stats.norm.cdf((crit - p1) / np.sqrt(p1 * (1 - p1) / n)))

    if method == "exact":
        # Exact binomial: find the rejection region under p0, then its
        # probability under p1.
        if direction == "above":
            # smallest k with P(X >= k | p0) <= alpha
            k = stats.binom.isf(alpha, n, p0)  # upper-tail inverse
            k = int(np.ceil(k))
            k = min(max(k, 0), n + 1)
            return float(stats.binom.sf(k - 1, n, p1))  # P(X >= k | p1)
        k = stats.binom.ppf(alpha, n, p0)
        k = int(np.floor(k))
        k = min(max(k, -1), n)
        return float(stats.binom.cdf(k, n, p1))  # P(X <= k | p1)

    raise ValueError("method must be 'normal' or 'exact'")


def required_n(p0, p1, alpha=0.05, power=0.95, direction="above"):
    """Sample size to detect ``p1`` vs threshold ``p0`` at target ``power``.

    Standard one-sided one-sample proportion formula:
        n = ( z_alpha sqrt(p0 q0) + z_beta sqrt(p1 q1) )^2 / (p1 - p0)^2
    Returns an integer (rounded up).
    """
    if p1 == p0:
        raise ValueError("p1 must differ from p0 (no effect to detect)")
    za = _z(alpha)
    zb = _z(1.0 - power)
    num = za * np.sqrt(p0 * (1 - p0)) + zb * np.sqrt(p1 * (1 - p1))
    n = (num ** 2) / (p1 - p0) ** 2
    return int(np.ceil(n))


def minimum_detectable_effect(n, p0, alpha=0.05, power=0.95, direction="above"):
    """Smallest true rate distinguishable from ``p0`` at given ``n`` and power.

    Solves ``power_vs_threshold(n, p0, p1) == power`` for ``p1`` on the danger
    side of the threshold. Returns ``p1`` (the MDE is ``abs(p1 - p0)``).
    """
    from scipy.optimize import brentq

    def gap(p1):
        return power_vs_threshold(n, p0, p1, alpha, direction, "normal") - power

    if direction == "above":
        lo, hi = p0 + 1e-9, 1.0 - 1e-9
    else:
        lo, hi = 1e-9, p0 - 1e-9
    # power is monotone in p1 away from p0; if even the extreme can't reach the
    # target power, the effect is undetectable at this n.
    if gap(hi if direction == "above" else lo) < 0:
        return float("nan")
    p1 = brentq(gap, lo, hi, xtol=1e-6)
    return float(p1)
