#!/usr/bin/env python
"""Empirical coverage and threshold behaviour of the ratio-of-means intervals.

The uplift analysis (``scripts/uplift_analysis.py``) reports intervals for the
ratio of arm means: delta (linearised), Fieller (exact-test inversion), and a
scaled-Beta parametric bootstrap. Each is only as good as its coverage at
n = 8-10, where CLT-based intervals are known to misbehave (Bowyer 2025). This
script measures that behaviour directly, and it does so honestly about the two
modelling choices that move the answer:

  1. The critical value. The headline table reports the small-sample
     t(df = n-1) interval, so we calibrate THAT interval: every interval below
     is built with ``df = n-1``, not a normal z. (Under a z critical value the
     same intervals under-cover by ~0.03; near-nominal coverage is therefore a
     property of the t construction, not a free lunch.)

  2. The data-generating process. A smooth scaled-Beta matched to (mean, sd) is
     a best-case; a real rubric is lumpier. We therefore run each condition
     under BOTH a scaled-Beta DGP and a floor-clustered two-point DGP matched to
     the same (mean, sd), and report both.

We report two quantities:

  * coverage of the TRUE generating ratio (a calibration check); and
  * the threshold operating characteristic -- when the true ratio sits AT a
    decision line tau, the coverage of tau and the "false-safe" rate
    P(interval lies entirely below tau), the quantity a below-the-line
    conformity claim would rest on.

Output: a table-ready CSV plus a console summary. Fixed seed for reproducibility.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402

from evalaudit.ratio import delta_log_ratio_ci, fieller_ci  # noqa: E402
from evalaudit.uplift import match_scaled_beta  # noqa: E402

M_CONTROL = 25.0
M_TREAT = 63.0
SPREAD = 13.0
SUPPORT = 100.0
TRUE_RATIO = M_TREAT / M_CONTROL

N_REPLICATES = 20000
SEED = 12345
OUTFILE = Path(__file__).resolve().parents[1] / "data" / "derived" / "coverage_sim.csv"

# reading -> participant-level SD implied for the arms (for the generating model)
READINGS = {
    "SD": {8: SPREAD, 9: SPREAD, 10: SPREAD},              # ±13 is a participant SD
    "SE": {9: SPREAD * math.sqrt(9)},                      # ±13 is the SE of the mean
    "CI half-width": {9: (SPREAD / 1.96) * math.sqrt(9)},  # ±13 is a 95%-CI half-width
}


def arm_se(sample):
    """Standard error of an arm mean from a sample (unbiased SD / sqrt(n))."""
    return float(np.std(sample, ddof=1) / math.sqrt(len(sample)))


def draw_arm(rng, mean, sd, dgp, size):
    """Draw an (N_REPLICATES x n) arm from the chosen DGP, matched to (mean, sd).

    ``beta`` is the smooth scaled-Beta on [0, SUPPORT] (best case). ``two_point``
    is a floor-clustered distribution with mass at 0 and at H = mean + sd^2/mean
    (probability p = mean/H); it matches the same mean and sd but is the lumpy,
    near-binary shape an uplift rubric plausibly produces. Returns None if the
    DGP is infeasible on the bounded support.
    """
    if dgp == "beta":
        m = match_scaled_beta(mean, sd, SUPPORT)
        if not m.feasible:
            return None
        return SUPPORT * rng.beta(m.a, m.b, size=size)
    if dgp == "two_point":
        if mean <= 0:
            return None
        H = mean + sd**2 / mean
        if H > SUPPORT or H <= 0:
            return None
        p = mean / H
        return rng.binomial(1, p, size=size) * H
    raise ValueError(dgp)


def simulate(mc, mt, participant_sd, n, dgp, truth, use_t=True):
    """Coverage of ``truth`` and the false-safe rate for a two-arm ratio.

    Arms are drawn from ``dgp`` matched to means (mc, mt) and SD ``participant_sd``
    at size n. Intervals use the small-sample t(df = n-1) critical value when
    ``use_t`` (the interval the paper reports), else the normal z -- reported side
    by side so the z-vs-t sensitivity is explicit. Returns coverage and
    P(interval entirely below truth) for delta and Fieller, plus the
    unbounded-Fieller fraction.
    """
    rng = np.random.default_rng(SEED)
    treat = draw_arm(rng, mt, participant_sd, dgp, (N_REPLICATES, n))
    control = draw_arm(rng, mc, participant_sd, dgp, (N_REPLICATES, n))
    if treat is None or control is None:
        return None

    df = (n - 1) if use_t else None
    cover = {"delta": 0, "fieller": 0}
    below = {"delta": 0, "fieller": 0}
    unbounded_fieller = 0
    used = 0
    for i in range(N_REPLICATES):
        t, c = treat[i], control[i]
        mt_i, mc_i = float(t.mean()), float(c.mean())
        if mc_i <= 0:
            continue
        used += 1
        set_, sec = arm_se(t), arm_se(c)

        _, dlo, dhi = delta_log_ratio_ci(mt_i, set_, mc_i, sec, alpha=0.05, df=df)
        if dlo <= truth <= dhi:
            cover["delta"] += 1
        if dhi < truth:
            below["delta"] += 1

        f = fieller_ci(mt_i, set_, mc_i, sec, alpha=0.05, df=df)
        if f.kind != "bounded":
            unbounded_fieller += 1
        if f.low <= truth <= f.high:
            cover["fieller"] += 1
        if f.kind == "bounded" and f.high < truth:
            below["fieller"] += 1

    return {
        "delta_coverage": cover["delta"] / used,
        "fieller_coverage": cover["fieller"] / used,
        "delta_below_frac": below["delta"] / used,
        "fieller_below_frac": below["fieller"] / used,
        "unbounded_fieller_frac": unbounded_fieller / used,
    }


def main():
    rows = []
    print(f"Ratio-of-means interval behaviour, t(df=n-1) intervals, "
          f"{N_REPLICATES} replicates, arms on [0,{SUPPORT:.0f}]\n")

    # ---- Calibration: coverage of the true generating ratio (2.52x). ------- #
    # Beta DGP under both t and z (to expose the z-vs-t sensitivity); the lumpy
    # two-point DGP under t (the interval the paper reports).
    print("== Coverage of the true ratio "
          f"{TRUE_RATIO:.2f}x (calibration) ==")
    print(f"{'reading':<14}{'n':>3} {'part.SD':>8} {'dgp':>10} {'crit':>5}  "
          f"{'delta':>7} {'fieller':>7} {'unb.F':>6}")
    conditions = [("beta", True), ("beta", False), ("two_point", True)]
    for reading, by_n in READINGS.items():
        for n, participant_sd in by_n.items():
            for dgp, use_t in conditions:
                crit = "t" if use_t else "z"
                res = simulate(M_CONTROL, M_TREAT, participant_sd, n, dgp,
                               TRUE_RATIO, use_t=use_t)
                feasible = res is not None
                if not feasible:
                    bound = math.sqrt(M_CONTROL * (SUPPORT - M_CONTROL))
                    print(f"{reading:<14}{n:>3} {participant_sd:>8.1f} {dgp:>10} "
                          f"{crit:>5}  INFEASIBLE (SD > bound {bound:.1f} at mean 25)")
                    rows.append({
                        "kind": "coverage", "reading": reading, "n": n,
                        "participant_sd": round(participant_sd, 2), "dgp": dgp,
                        "crit": crit, "truth_ratio": round(TRUE_RATIO, 3),
                        "delta_coverage": "n/a", "fieller_coverage": "n/a",
                        "delta_below_frac": "n/a", "fieller_below_frac": "n/a",
                        "unbounded_fieller_frac": "n/a", "feasible": False,
                    })
                    continue
                print(f"{reading:<14}{n:>3} {participant_sd:>8.1f} {dgp:>10} {crit:>5}  "
                      f"{res['delta_coverage']:>7.3f} {res['fieller_coverage']:>7.3f} "
                      f"{res['unbounded_fieller_frac']:>6.3f}")
                rows.append({
                    "kind": "coverage", "reading": reading, "n": n,
                    "participant_sd": round(participant_sd, 2), "dgp": dgp,
                    "crit": crit, "truth_ratio": round(TRUE_RATIO, 3),
                    "delta_coverage": round(res["delta_coverage"], 4),
                    "fieller_coverage": round(res["fieller_coverage"], 4),
                    "delta_below_frac": round(res["delta_below_frac"], 4),
                    "fieller_below_frac": round(res["fieller_below_frac"], 4),
                    "unbounded_fieller_frac": round(res["unbounded_fieller_frac"], 4),
                    "feasible": True,
                })

    # ---- Threshold operating characteristic: truth AT a decision line. ----- #
    # SD reading (participant SD = 13), n = 9, control mean 15 so that even the
    # 5x line keeps both arms inside [0,100]. "false-safe" = P(interval entirely
    # below tau), the error a below-the-line conformity claim would commit.
    print("\n== Threshold operating characteristic (SD reading, n=9, "
          "false-safe = P[interval entirely below tau]) ==")
    print(f"{'tau':>5} {'dgp':>10}  {'F.cover':>8} {'F.below':>8} "
          f"{'d.cover':>8} {'d.below':>8} {'unb.F':>6}")
    oc_mc = 15.0
    for tau in (2.8, 5.0):
        for dgp in ("beta", "two_point"):
            res = simulate(oc_mc, oc_mc * tau, SPREAD, 9, dgp, tau)
            if res is None:
                print(f"{tau:>5.1f} {dgp:>10}  INFEASIBLE")
                continue
            print(f"{tau:>5.1f} {dgp:>10}  {res['fieller_coverage']:>8.3f} "
                  f"{res['fieller_below_frac']:>8.3f} {res['delta_coverage']:>8.3f} "
                  f"{res['delta_below_frac']:>8.3f} {res['unbounded_fieller_frac']:>6.3f}")
            rows.append({
                "kind": "threshold_oc", "reading": "SD", "n": 9,
                "participant_sd": round(SPREAD, 2), "dgp": dgp, "crit": "t",
                "truth_ratio": round(tau, 3),
                "delta_coverage": round(res["delta_coverage"], 4),
                "fieller_coverage": round(res["fieller_coverage"], 4),
                "delta_below_frac": round(res["delta_below_frac"], 4),
                "fieller_below_frac": round(res["fieller_below_frac"], 4),
                "unbounded_fieller_frac": round(res["unbounded_fieller_frac"], 4),
                "feasible": True,
            })

    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTFILE.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nNominal coverage is 0.95. wrote {OUTFILE}")


if __name__ == "__main__":
    main()
