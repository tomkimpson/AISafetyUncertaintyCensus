"""Confidence intervals for a ratio of two quantities.

Two distinct estimands live here, and the distinction matters:

* ``risk_ratio_ci`` — ratio of two *proportions* (Katz log method). Appropriate
  when each arm reports a success count over a Bernoulli denominator.

* ``delta_log_ratio_ci`` and ``fieller_ci`` — ratio of two *means* of a
  continuous score. The Opus 4 bio-uplift trial reports arm *averages* of a
  continuous Deloitte rubric (25% / 63%), so its ``2.53×`` uplift is a
  ratio-of-means, not a ratio-of-proportions. The delta method linearises
  ``log(m1/m0)``; Fieller's theorem inverts the exact test and, unlike the
    delta method, correctly returns a *disjoint* set when the denominator mean
  is not significantly different from zero at the chosen level. At the trial's
  sample sizes the control arm sits right at that boundary (25/13 ≈ 1.92 < 1.96),
  so Fieller is the honest headline and the delta interval is a linearisation
  check. See Fieller (1954).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


def _crit(alpha, df=None):
    """Two-sided critical value: t(df) if df given, else normal z."""
    if df is not None:
        return float(stats.t.ppf(1 - alpha / 2, df))
    return float(stats.norm.ppf(1 - alpha / 2))


def delta_log_ratio_ci(m1, se1, m0, se0, alpha=0.05, df=None):
    """Delta-method CI for the ratio of two independent means ``m1 / m0``.

    Linearises ``log(m1/m0)`` with ``SE = sqrt((se1/m1)^2 + (se0/m0)^2)`` and
    exponentiates. Returns ``(ratio, low, high)``. This is a *check*, not the
    headline: it is a first-order approximation that stays finite even when the
    exact (Fieller) set is unbounded, so it understates uncertainty when the
    denominator is imprecise. Pass ``df`` to use a t critical value at small n.
    """
    if m1 <= 0 or m0 <= 0:
        raise ValueError("means must be positive for a log-ratio interval")
    r = m1 / m0
    se_log = np.sqrt((se1 / m1) ** 2 + (se0 / m0) ** 2)
    c = _crit(alpha, df)
    lo = float(np.exp(np.log(r) - c * se_log))
    hi = float(np.exp(np.log(r) + c * se_log))
    return float(r), lo, hi


@dataclass(frozen=True)
class FiellerResult:
    """Fieller confidence set for a ratio of two independent means.

    ``kind`` is one of:

    ``components`` preserves the complete confidence set as closed intervals.
    In particular, when ``g >= 1`` the set is ordinarily two disjoint rays,
    ``(-inf, a] U [b, inf)``. It must not be collapsed to the ray containing the
    point estimate. ``restrict_nonnegative`` may be used only when a
    nonnegative-ratio parameter space is substantively justified.

    ``g = (crit * se0 / m0)^2`` is the denominator's relative variance; ``g >= 1``
    is exactly the condition ``m0 / se0 <= crit`` under which the ratio cannot be
    bounded above.
    """

    ratio: float
    components: tuple[tuple[float, float], ...]
    kind: str
    g: float

    def straddles(self, threshold: float) -> bool:
        """True if any component of the set contains ``threshold``."""
        return any(low <= threshold <= high for low, high in self.components)

    @property
    def low(self) -> float:
        """Lower endpoint for a connected set; reject ambiguous disjoint sets."""
        if len(self.components) != 1:
            raise ValueError("disjoint Fieller set has no single lower endpoint")
        return self.components[0][0]

    @property
    def high(self) -> float:
        """Upper endpoint for a connected set; reject ambiguous disjoint sets."""
        if len(self.components) != 1:
            raise ValueError("disjoint Fieller set has no single upper endpoint")
        return self.components[0][1]

    def restrict_nonnegative(self) -> "FiellerResult":
        """Intersect the confidence set with the justified parameter space [0, inf)."""
        components = tuple(
            (max(0.0, low), high)
            for low, high in self.components
            if max(0.0, low) <= high
        )
        if not components:
            kind = "empty"
        elif len(components) > 1:
            kind = "disjoint"
        else:
            low, high = components[0]
            if np.isneginf(low) and np.isposinf(high):
                kind = "all_real"
            elif np.isposinf(high):
                kind = "unbounded_above"
            elif np.isneginf(low):
                kind = "unbounded_below"
            else:
                kind = "bounded"
        return FiellerResult(self.ratio, components, kind, self.g)


def fieller_ci(m1, se1, m0, se0, alpha=0.05, df=None, cov=0.0):
    """Fieller's-theorem confidence set for the ratio of two means.

    Solves ``(m1 - rho*m0)^2 <= crit^2 (se1^2 - 2*rho*cov + rho^2 se0^2)`` for
    ``rho``. ``cov`` is the covariance of the two arm means; it defaults to ``0``
    (independent arms, the reported case). Pass ``cov = corr * se1 * se0`` to
    probe how a paired / positively-correlated design would move the interval.
    Returns a :class:`FiellerResult`. When the denominator mean is not
    significantly different from zero at level ``alpha`` (``g >= 1``) the set is
    generally disjoint on the real line. The caller may then intersect it with
    a substantively justified parameter space such as nonnegative ratios.
    """
    if m0 <= 0:
        raise ValueError("denominator mean must be positive")
    c = _crit(alpha, df)
    a = m0**2 - c**2 * se0**2
    b = -2.0 * (m1 * m0 - c**2 * cov)
    cc = m1**2 - c**2 * se1**2
    g = float((c**2 * se0**2) / m0**2)
    r = float(m1 / m0)
    disc = b**2 - 4.0 * a * cc

    if a > 0:
        # Parabola opens upward: solution set is between the roots (if any).
        if disc < 0:
            return FiellerResult(r, (), "empty", g)
        root = np.sqrt(disc)
        lo = (-b - root) / (2 * a)
        hi = (-b + root) / (2 * a)
        component = (float(min(lo, hi)), float(max(lo, hi)))
        return FiellerResult(r, (component,), "bounded", g)

    if a < 0:
        # Denominator not significant (g >= 1): parabola opens downward, so the
        # solution set is the COMPLEMENT of the interval between the roots.
        if disc <= 0:
            return FiellerResult(r, ((float("-inf"), float("inf")),), "all_real", g)
        root = np.sqrt(disc)
        r1 = (-b - root) / (2 * a)
        r2 = (-b + root) / (2 * a)
        lo_root, hi_root = min(r1, r2), max(r1, r2)
        components = (
            (float("-inf"), float(lo_root)),
            (float(hi_root), float("inf")),
        )
        return FiellerResult(r, components, "disjoint", g)

    # Exact boundary: solve the remaining linear inequality b*rho + cc <= 0.
    if b > 0:
        return FiellerResult(
            r, ((float("-inf"), float(-cc / b)),), "unbounded_below", g
        )
    if b < 0:
        return FiellerResult(
            r, ((float(-cc / b), float("inf")),), "unbounded_above", g
        )
    if cc <= 0:
        return FiellerResult(r, ((float("-inf"), float("inf")),), "all_real", g)
    return FiellerResult(r, (), "empty", g)


def risk_ratio_ci(p_treat, n_treat, p_control, n_control, alpha=0.05):
    """Katz-log CI for the risk ratio ``p_treat / p_control``.

    Parameters are the two arms' success proportions and sample sizes. Returns
    ``(ratio, low, high)``. Requires non-zero proportions (the log method is
    undefined at a zero cell; report that separately if it occurs).
    """
    if not (0 < p_treat <= 1 and 0 < p_control <= 1):
        raise ValueError("proportions must be in (0, 1]")
    if n_treat < 1 or n_control < 1:
        raise ValueError("sample sizes must be >= 1")
    rr = p_treat / p_control
    # SE of log(RR) = sqrt((1-p1)/(n1 p1) + (1-p2)/(n2 p2)).
    se_log = np.sqrt(
        (1 - p_treat) / (n_treat * p_treat)
        + (1 - p_control) / (n_control * p_control)
    )
    z = stats.norm.ppf(1 - alpha / 2)
    lo = float(np.exp(np.log(rr) - z * se_log))
    hi = float(np.exp(np.log(rr) + z * se_log))
    return float(rr), lo, hi
