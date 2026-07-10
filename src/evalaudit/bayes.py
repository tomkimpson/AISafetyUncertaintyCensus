"""Bayesian mirror: Beta-Binomial posterior over the true capability rate.

The frequentist test asks "can we reject that the model sits at the threshold?"
The Bayesian view asks the question governance actually cares about: given the
data, what is the probability the true capability exceeds the threshold? If that
posterior probability is neither near 0 nor near 1, the eval has not resolved
the decision — regardless of one's stance on hypothesis testing.

Default prior is uniform Beta(1, 1). Jeffreys Beta(0.5, 0.5) is available for a
less informative alternative; robustness tables should report both.
"""

from __future__ import annotations

from scipy import stats


def beta_binomial_posterior(successes, n, prior=(1.0, 1.0)):
    """Posterior Beta parameters after observing ``successes`` of ``n``.

    Returns ``(a_post, b_post)`` for ``Beta(a0 + s, b0 + n - s)``.
    """
    a0, b0 = prior
    if a0 <= 0 or b0 <= 0:
        raise ValueError("prior parameters must be positive")
    if not (0 <= successes <= n):
        raise ValueError("successes must be in [0, n]")
    return a0 + successes, b0 + (n - successes)


def prob_above(threshold, successes, n, prior=(1.0, 1.0)):
    """Posterior probability that the true rate exceeds ``threshold``."""
    a, b = beta_binomial_posterior(successes, n, prior)
    return float(stats.beta.sf(threshold, a, b))


def credible_interval(successes, n, alpha=0.05, prior=(1.0, 1.0)):
    """Equal-tailed ``(1 - alpha)`` credible interval."""
    a, b = beta_binomial_posterior(successes, n, prior)
    return float(stats.beta.ppf(alpha / 2, a, b)), float(
        stats.beta.ppf(1 - alpha / 2, a, b)
    )
