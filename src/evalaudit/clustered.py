"""Clustering corrections for eval scores.

Eval items are rarely independent: questions share a source document, a topic,
or a task template. Treating ``n`` correlated items as ``n`` independent
Bernoulli trials understates the variance. Following Miller (2024,
arXiv:2411.00640), we compute a cluster-robust standard error and translate it
into an *effective* sample size, which is what the eval's precision really
behaves like.
"""

from __future__ import annotations

import numpy as np

from .intervals import proportion_ci, proportion_directional_bounds, straddles


def cluster_robust_se(cluster_successes, cluster_sizes):
    """Cluster-robust standard error of the overall proportion.

    Uses the standard linearization (sandwich, CR1) estimator for the mean of
    clustered binary data. Equivalent to regressing the 0/1 outcome on an
    intercept with cluster-robust errors.

    Parameters
    ----------
    cluster_successes : array-like of int
        Successes within each cluster.
    cluster_sizes : array-like of int
        Item count within each cluster (same length).

    Returns
    -------
    (p_hat, se) : tuple of float
        Overall proportion and its cluster-robust SE.
    """
    s = np.asarray(cluster_successes, dtype=float)
    m = np.asarray(cluster_sizes, dtype=float)
    if s.shape != m.shape:
        raise ValueError("cluster_successes and cluster_sizes must align")
    if np.any(s > m) or np.any(s < 0):
        raise ValueError("each cluster's successes must be in [0, size]")
    G = len(m)
    if G < 2:
        raise ValueError("need >= 2 clusters for a cluster-robust SE")
    N = m.sum()
    p_hat = s.sum() / N
    # Cluster score = successes - expected under p_hat = sum of residuals.
    u = s - m * p_hat
    # CR1 small-sample adjustment G/(G-1).
    var = (G / (G - 1.0)) * np.sum(u ** 2) / (N ** 2)
    return float(p_hat), float(np.sqrt(var))


def design_effect(cluster_sizes, icc):
    """Design effect ``DEFF = 1 + (m_bar - 1) * ICC`` for equal-ish clusters.

    ``m_bar`` is the average cluster size. ICC is the intra-cluster
    correlation. DEFF is the factor by which the variance inflates relative to
    simple random sampling.
    """
    m = np.asarray(cluster_sizes, dtype=float)
    if not (0.0 <= icc <= 1.0):
        raise ValueError("icc must be in [0, 1]")
    m_bar = m.mean()
    return float(1.0 + (m_bar - 1.0) * icc)


def effective_n(n, deff=None, se_clustered=None, p_hat=None):
    """Effective sample size.

    Either supply a design effect ``deff`` (``n_eff = n / deff``), or supply a
    clustered SE together with ``p_hat`` to back out the independent-trial
    count that would produce the same variance:
    ``n_eff = p_hat (1 - p_hat) / se_clustered**2``.
    """
    if deff is not None:
        if deff <= 0:
            raise ValueError("deff must be positive")
        return float(n / deff)
    if se_clustered is not None and p_hat is not None:
        if se_clustered <= 0:
            raise ValueError("se_clustered must be positive")
        return float(p_hat * (1.0 - p_hat) / se_clustered ** 2)
    raise ValueError("supply either deff, or (se_clustered and p_hat)")


def clustered_ci(score, n, deff, alpha=0.05, method="wilson"):
    """CI for a proportion recomputed at effective n = ``n / deff``.

    Uses fractional pseudo-counts ``(score * n_eff, n_eff)``; exact-method
    intervals become generalized (non-integer) intervals. Requires
    ``n / deff >= 1`` so the pseudo-sample stays meaningful.

    Returns
    -------
    (low, high) : tuple of float
    """
    if not (0.0 <= score <= 1.0):
        raise ValueError("score must be in [0, 1]")
    if deff < 1.0:
        raise ValueError("deff must be >= 1 (clustering cannot add information)")
    n_eff = effective_n(n, deff=deff)
    if n_eff < 1.0:
        raise ValueError(f"deff={deff} leaves effective n {n_eff:.2f} < 1")
    return proportion_ci(score * n_eff, n_eff, alpha=alpha, method=method)


def clustered_directional_bounds(score, n, deff, alpha=0.05, method="wilson"):
    """One-sided ``(1 - alpha)`` bounds at effective ``n / deff``."""
    if not (0.0 <= score <= 1.0):
        raise ValueError("score must be in [0, 1]")
    if deff < 1.0:
        raise ValueError("deff must be >= 1 (clustering cannot add information)")
    n_eff = effective_n(n, deff=deff)
    if n_eff < 1.0:
        raise ValueError(f"deff={deff} leaves effective n {n_eff:.2f} < 1")
    return proportion_directional_bounds(
        score * n_eff, n_eff, alpha=alpha, method=method
    )


def critical_deff(
    score,
    n,
    threshold,
    alpha=0.05,
    method="wilson",
    step=0.01,
    directional=True,
):
    """Smallest design effect at which the CI straddles the threshold.

    The CI is recomputed at ``n_eff = n / deff`` with the same point estimate,
    so this is the clustering severity needed to turn a demonstrated
    directional claim into indeterminacy. Returns 1.0 if the naive bounds
    already straddle, and None
    if no deff in ``[1, n]`` flips it (possible only for thresholds at or near
    the [0, 1] boundary, since at ``n_eff = 1`` the interval spans nearly the
    whole unit interval).

    A linear scan (not bisection) so no monotonicity assumption is needed.
    """
    deff = 1.0
    interval_fn = clustered_directional_bounds if directional else clustered_ci
    while deff <= n:
        if straddles(threshold, interval_fn(score, n, deff, alpha, method)):
            return float(deff)
        deff += step
    return None
