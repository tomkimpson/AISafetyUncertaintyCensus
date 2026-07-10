"""evalaudit — statistical resolving power of dangerous-capability evals.

Given a published eval result (n trials, observed score) and a governance
threshold, quantify whether the number can actually place a model on one side
of that threshold, and how many trials it would take to do so.

Public entry point: :func:`evalaudit.audit.audit`.
"""

from .intervals import proportion_ci, bootstrap_ci
from .clustered import (
    cluster_robust_se,
    clustered_ci,
    critical_deff,
    design_effect,
    effective_n,
)
from .power import power_vs_threshold, required_n, minimum_detectable_effect
from .bayes import beta_binomial_posterior, prob_above, credible_interval
from .ratio import (
    risk_ratio_ci,
    delta_log_ratio_ci,
    fieller_ci,
    FiellerResult,
)
from .uplift import (
    bhatia_davis_max_sd,
    match_scaled_beta,
    bootstrap_ratio_ci,
    BetaMatch,
)
from .audit import audit, AuditResult

__all__ = [
    "proportion_ci",
    "bootstrap_ci",
    "cluster_robust_se",
    "clustered_ci",
    "critical_deff",
    "design_effect",
    "effective_n",
    "power_vs_threshold",
    "required_n",
    "minimum_detectable_effect",
    "beta_binomial_posterior",
    "prob_above",
    "credible_interval",
    "risk_ratio_ci",
    "delta_log_ratio_ci",
    "fieller_ci",
    "FiellerResult",
    "bhatia_davis_max_sd",
    "match_scaled_beta",
    "bootstrap_ratio_ci",
    "BetaMatch",
    "audit",
    "AuditResult",
]
