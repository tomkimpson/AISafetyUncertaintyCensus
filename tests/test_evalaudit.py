"""Correctness tests against hand-computed / textbook reference values."""

import math

import numpy as np
import pytest

from evalaudit import (
    risk_ratio_ci,
    delta_log_ratio_ci,
    fieller_ci,
    bhatia_davis_max_sd,
    match_scaled_beta,
    bootstrap_ratio_ci,
    proportion_ci,
    proportion_directional_bounds,
    cluster_robust_se,
    clustered_ci,
    clustered_directional_bounds,
    critical_deff,
    design_effect,
    effective_n,
    power_vs_threshold,
    required_n,
    minimum_detectable_effect,
    prob_above,
    credible_interval,
    beta_binomial_posterior,
    audit,
)
from evalaudit.intervals import straddles


# ---------------------------------------------------------------- intervals
def test_wilson_50_of_20():
    # Textbook Wilson 95% CI for 10/20 is ~(0.299, 0.701), centered on 0.5.
    lo, hi = proportion_ci(10, 20, alpha=0.05, method="wilson")
    assert lo == pytest.approx(0.299, abs=1e-3)
    assert hi == pytest.approx(0.701, abs=1e-3)
    assert (lo + hi) / 2 == pytest.approx(0.5, abs=1e-6)


def test_clopper_pearson_zero_successes():
    # For x=0, exact upper limit = 1 - (alpha/2)^(1/n).
    n = 10
    lo, hi = proportion_ci(0, n, alpha=0.05, method="beta")
    assert lo == 0.0
    assert hi == pytest.approx(1 - 0.025 ** (1 / n), abs=1e-6)  # ~0.3085


def test_clopper_pearson_wider_than_wilson():
    w = proportion_ci(42, 100, method="wilson")
    cp = proportion_ci(42, 100, method="beta")
    assert cp[0] <= w[0] and cp[1] >= w[1]  # exact interval is conservative


def test_straddles():
    assert straddles(0.5, (0.4, 0.6))
    assert not straddles(0.5, (0.51, 0.6))
    assert straddles(0.5, (0.5, 0.6))  # equality does not establish a side


def test_directional_bounds_are_central_90_percent_endpoints():
    directional = proportion_directional_bounds(42, 100, alpha=0.05)
    central_90 = proportion_ci(42, 100, alpha=0.10)
    assert directional == pytest.approx(central_90)


# ---------------------------------------------------------------- clustering
def test_cluster_robust_reduces_to_binomial_for_singletons():
    # Clusters of size 1: SE = naive * sqrt(G/(G-1)).
    G = 100
    successes = [1] * 30 + [0] * 70  # p_hat = 0.30
    sizes = [1] * G
    p_hat, se = cluster_robust_se(successes, sizes)
    assert p_hat == pytest.approx(0.30)
    se_naive = math.sqrt(0.3 * 0.7 / G)
    assert se == pytest.approx(se_naive * math.sqrt(G / (G - 1)), rel=1e-6)


def test_cluster_inflation_with_between_cluster_variance():
    # Perfectly homogeneous-within, heterogeneous-between clusters inflate SE
    # far above the naive binomial value.
    sizes = [20] * 10
    successes = [20] * 5 + [0] * 5  # half all-correct, half all-wrong; p=0.5
    p_hat, se = cluster_robust_se(successes, sizes)
    assert p_hat == pytest.approx(0.5)
    se_naive = math.sqrt(0.5 * 0.5 / 200)
    # ICC=1 gives the maximal design effect ~ (G/(G-1))*m = 22.2, i.e. SE ~4.7x.
    assert se > 4 * se_naive  # massive design effect


def test_design_effect_and_effective_n():
    assert design_effect([10] * 50, icc=0.1) == pytest.approx(1.9)
    assert effective_n(1000, deff=1.9) == pytest.approx(1000 / 1.9)
    # via clustered SE round trip
    assert effective_n(100, se_clustered=math.sqrt(0.25 / 25), p_hat=0.5) == pytest.approx(25)


# ---------------------------------------------------------------- clustered sweep
def test_clustered_ci_deff1_matches_proportion_ci():
    lo, hi = clustered_ci(17 / 42, 42, deff=1.0)
    lo0, hi0 = proportion_ci(17, 42)
    assert lo == pytest.approx(lo0, abs=1e-9)
    assert hi == pytest.approx(hi0, abs=1e-9)


def test_clustered_ci_widens_with_deff():
    inner = clustered_ci(0.4, 42, deff=1.0)
    outer = clustered_ci(0.4, 42, deff=4.0)
    assert outer[0] < inner[0] and outer[1] > inner[1]


def test_clustered_ci_rejects_neff_below_1():
    with pytest.raises(ValueError):
        clustered_ci(0.4, 42, deff=50.0)  # n_eff < 1
    with pytest.raises(ValueError):
        clustered_ci(0.4, 42, deff=0.5)  # deff < 1 would add information


def test_critical_deff_is_one_when_already_straddling():
    # The indeterminate fixture: 0.42 on n=100 straddles 0.5 already.
    assert critical_deff(0.42, 100, 0.5) == 1.0


def test_critical_deff_flip_is_real():
    score, n, thr = 10 / 42, 42, 0.5
    cd = critical_deff(score, n, thr)
    assert cd is not None and cd > 1.0
    assert straddles(thr, clustered_directional_bounds(score, n, cd))
    assert not straddles(
        thr, clustered_directional_bounds(score, n, max(1.0, cd - 0.05))
    )


def test_critical_deff_monotone_in_gap():
    # Farther from the threshold -> more clustering needed to blur the verdict.
    cds = [critical_deff(s, 100, 0.5) for s in (0.40, 0.30, 0.20)]
    assert cds[0] < cds[1] < cds[2]


def test_critical_icc_translation():
    # critical_icc = (deff - 1) / (m - 1) inverts design_effect for equal clusters.
    assert design_effect([10], (2.8 - 1) / 9) == pytest.approx(2.8)


def test_critical_deff_bioweapons_row():
    # Bioweapons row: 17/33 vs the 27/33 rule-out line. The primary one-sided
    # upper bound demonstrates below naively; pin its clustering flip point.
    cd = critical_deff(17 / 33, 33, 0.818)
    assert cd is not None and 1.0 < cd <= 33
    assert cd == pytest.approx(7.52, abs=0.05)


# ---------------------------------------------------------------- power
def test_power_at_threshold_equals_alpha():
    # A one-sided level-alpha test has power exactly alpha when p1 == p0.
    assert power_vs_threshold(100, 0.5, 0.5, alpha=0.05, method="normal") == pytest.approx(0.05, abs=1e-9)


def test_power_monotone_in_effect():
    p = [power_vs_threshold(100, 0.5, x) for x in (0.55, 0.60, 0.70)]
    assert p[0] < p[1] < p[2]


def test_required_n_matches_formula():
    # p0=0.5, p1=0.42, one-sided, alpha=0.05, power=0.95 -> ~418.
    assert required_n(0.5, 0.42, alpha=0.05, power=0.95) == 418


def test_required_n_roundtrips_to_power():
    n = required_n(0.5, 0.65, alpha=0.05, power=0.90)
    achieved = power_vs_threshold(n, 0.5, 0.65, alpha=0.05, method="normal")
    assert achieved >= 0.90


def test_mde_roundtrip():
    p1 = minimum_detectable_effect(100, 0.5, alpha=0.05, power=0.90, direction="above")
    assert power_vs_threshold(100, 0.5, p1, method="normal") == pytest.approx(0.90, abs=1e-3)


def test_exact_and_normal_power_agree_large_n():
    pn = power_vs_threshold(1000, 0.5, 0.58, method="normal")
    pe = power_vs_threshold(1000, 0.5, 0.58, method="exact")
    assert abs(pn - pe) < 0.03


# ---------------------------------------------------------------- bayes
def test_posterior_params():
    a, b = beta_binomial_posterior(10, 20, prior=(1, 1))
    assert (a, b) == (11, 11)


def test_prob_above_symmetric():
    # Uniform prior, 10/20, threshold 0.5 -> posterior symmetric -> P=0.5.
    assert prob_above(0.5, 10, 20, prior=(1, 1)) == pytest.approx(0.5, abs=1e-9)


def test_jeffreys_credible_matches_statsmodels():
    # Bayesian equal-tailed interval with Jeffreys prior == statsmodels
    # 'jeffreys' frequentist interval (they are the same construction).
    ours = credible_interval(42, 100, alpha=0.05, prior=(0.5, 0.5))
    sm = proportion_ci(42, 100, alpha=0.05, method="jeffreys")
    assert ours[0] == pytest.approx(sm[0], abs=1e-9)
    assert ours[1] == pytest.approx(sm[1], abs=1e-9)


# ---------------------------------------------------------------- risk ratio
def test_risk_ratio_point_and_symmetry():
    rr, lo, hi = risk_ratio_ci(0.63, 9, 0.25, 9, alpha=0.05)
    assert rr == pytest.approx(0.63 / 0.25)
    # CI is symmetric on the log scale.
    assert math.log(rr) - math.log(lo) == pytest.approx(math.log(hi) - math.log(rr), rel=1e-9)


def test_risk_ratio_wide_for_small_arms():
    # Generic Katz risk-ratio on two small-n proportions: tiny denominators ->
    # very wide log-scale CI. (This is the proportion-ratio helper; the Opus 4
    # bio-uplift trial itself is analysed as a ratio of continuous rubric MEANS
    # in scripts/uplift_analysis.py, not as a binomial proportion ratio.)
    rr, lo, hi = risk_ratio_ci(0.63, 9, 0.25, 9, alpha=0.05)
    assert lo < 1.0        # spans below 1x
    assert hi > 5.0        # spans past 5x


# ------------------------------------------------- ratio of means (uplift)
def test_delta_log_ratio_point_and_symmetry():
    r, lo, hi = delta_log_ratio_ci(63.0, 4.33, 25.0, 4.33, alpha=0.05)
    assert r == pytest.approx(63.0 / 25.0)
    # symmetric on the log scale
    assert math.log(r) - math.log(lo) == pytest.approx(math.log(hi) - math.log(r), rel=1e-9)


def test_fieller_bounded_agrees_with_delta_when_denominator_precise():
    # With a precise denominator (small se0 relative to m0), Fieller and the
    # delta method should nearly coincide.
    m1, m0, se = 63.0, 25.0, 1.0
    f = fieller_ci(m1, se, m0, se, alpha=0.05)
    _, dlo, dhi = delta_log_ratio_ci(m1, se, m0, se, alpha=0.05)
    assert f.kind == "bounded"
    assert f.low == pytest.approx(dlo, rel=0.02)
    assert f.high == pytest.approx(dhi, rel=0.02)


def test_fieller_unbounded_under_se_reading():
    # The whole-real-line set is two rays. Intersecting with the substantively
    # justified nonnegative-ratio space yields the displayed positive ray.
    f = fieller_ci(63.0, 13.0, 25.0, 13.0, alpha=0.05)
    assert f.kind == "disjoint"
    assert f.g > 1.0
    assert f.straddles(2.8) and f.straddles(5.0)
    assert f.components[0][1] == pytest.approx(-131.18, abs=0.1)
    positive = f.restrict_nonnegative()
    assert positive.kind == "unbounded_above"
    assert math.isinf(positive.high)
    assert positive.low == pytest.approx(1.05, abs=0.03)


def test_fieller_sd_reading_straddles_but_bounded():
    # Under the SD reading (SE = 13/sqrt(9)) the set is a bounded interval that
    # still straddles 2.8x.
    se = 13.0 / math.sqrt(9)
    f = fieller_ci(63.0, se, 25.0, se, alpha=0.05)
    assert f.kind == "bounded"
    assert f.low < 2.8 < f.high
    assert f.high < 5.0  # rules out the 5x significant-risk line


def test_fieller_t_wider_than_z():
    se = 13.0 / math.sqrt(9)
    fz = fieller_ci(63.0, se, 25.0, se, alpha=0.05, df=None)
    ft = fieller_ci(63.0, se, 25.0, se, alpha=0.05, df=8)
    assert ft.low < fz.low and ft.high > fz.high  # t interval is wider at small n


def test_bhatia_davis_bound():
    # Max SD on [0,100] at mean 25 is sqrt(25*75) ~= 43.3.
    assert bhatia_davis_max_sd(25.0, 100.0) == pytest.approx(math.sqrt(25 * 75))


def test_scaled_beta_infeasible_when_sd_exceeds_bound():
    # An SD of 39 at mean 25 on [0,100] is below the 43.3 ceiling -> feasible;
    # an SD of 45 exceeds it -> infeasible.
    assert match_scaled_beta(25.0, 39.0, 100.0).feasible is True
    assert match_scaled_beta(25.0, 45.0, 100.0).feasible is False


def test_scaled_beta_matches_mean_and_sd():
    m = match_scaled_beta(25.0, 13.0, 100.0)
    assert m.feasible
    # Beta(a,b) on [0,S]: mean = S*a/(a+b), var = S^2 ab/((a+b)^2 (a+b+1)).
    total = m.a + m.b
    mean = 100.0 * m.a / total
    var = 100.0**2 * m.a * m.b / (total**2 * (total + 1))
    assert mean == pytest.approx(25.0, abs=1e-6)
    assert math.sqrt(var) == pytest.approx(13.0, abs=1e-6)


def test_bootstrap_ratio_ci_reproducible_and_brackets_point():
    r1 = bootstrap_ratio_ci(63, 13, 9, 25, 13, 9, n_boot=4000, seed=0)
    r2 = bootstrap_ratio_ci(63, 13, 9, 25, 13, 9, n_boot=4000, seed=0)
    assert r1 == r2                      # deterministic under fixed seed
    ratio, lo, hi, feasible = r1
    assert feasible
    assert lo < ratio < hi


# ---------------------------------------------------------------- audit
def test_audit_indeterminate():
    r = audit(n=100, threshold=0.5, score=0.42)
    assert r.straddles_threshold is True
    assert r.verdict == "INDETERMINATE"
    assert r.decision_class == "INDETERMINATE"
    assert r.demonstrates_below is False
    assert r.demonstrates_above is False
    assert r.ci[0] < 0.5 < r.ci[1]
    assert r.required_n is not None and r.required_n > 100
    # posterior probability of being above threshold is far from 0 and 1
    assert 0.02 < r.prob_above < 0.98


def test_audit_demonstrates_below_when_far_from_threshold():
    r = audit(n=1000, threshold=0.5, score=0.20)
    assert r.straddles_threshold is False
    assert r.verdict == "BELOW DEMONSTRATED"
    assert r.demonstrates_below is True
    assert r.demonstrates_above is False
    assert r.prob_above < 0.001


def test_audit_demonstrates_above_when_far_from_threshold():
    r = audit(n=1000, threshold=0.5, score=0.80)
    assert r.straddles_threshold is False
    assert r.verdict == "ABOVE DEMONSTRATED"
    assert r.demonstrates_below is False
    assert r.demonstrates_above is True


def test_audit_accepts_successes_or_score():
    r1 = audit(n=200, threshold=0.5, successes=84)
    r2 = audit(n=200, threshold=0.5, score=0.42)
    assert r1.ci == pytest.approx(np.array(r2.ci))


def test_audit_with_clustering_shrinks_effective_n():
    sizes = [20] * 10
    successes = [14] * 10  # p=0.7 but homogeneous within, some between var if varied
    successes = [16, 12, 18, 10, 14, 15, 13, 17, 11, 14]  # p_hat=0.70
    r = audit(n=200, threshold=0.6, cluster=(successes, sizes))
    assert r.effective_n <= 200
