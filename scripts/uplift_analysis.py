#!/usr/bin/env python
"""The bio-uplift trial that was a central input to the Opus 4 ASL-3 decision.

Anthropic's Opus 4 System Card (§7.2.4.1; see the hashed source record in
``data/raw/sources/MANIFEST.md``) reports a human uplift
trial with three arms (control, Sonnet 4, Opus 4). Participant plans were
"graded by Deloitte using a detailed rubric that assesses key steps of the
acquisition pathway," and the card reports the arm *averages* of that continuous
rubric score: 25% ± 13% (control), 63% ± 13% (Opus 4), 42% ± 11% (Sonnet 4), for
a 2.53× / 1.70× uplift on arms of 8-10 participants. The trial's own threat
analysis (in that same section, NOT the RSP) treated ≤2.8× as keeping risk
acceptable and ≥5× as creating significant additional risk.

The scores are arm MEANS of a continuous rubric, so the 2.53× uplift is a
ratio-of-means. The card never labels the "±13%" (SD? SE? 95%-CI half-width? a
pooled/model-based SE?), and the reading changes the interval. We therefore
enumerate every admissible reading neutrally and, under each, report:

  * Fieller (the headline) -- inverts the exact test; returns an UNBOUNDED set
    when the denominator mean is not significant at the level, which is what the
    control arm does under the SE reading (25/13 ≈ 1.92 < 1.96);
  * the delta method (a linearisation check that stays finite even when Fieller
    is unbounded, hence understates uncertainty); and
  * a parametric bootstrap on scaled-Beta arms (no Normality assumption; also
    flags dispersions that are infeasible on the bounded [0,100] rubric).

The one verdict common to every reading is that the interval straddles the
binding 2.8× acceptable line. Per-participant scores are not published; arm
means and the "±13%" are as reported. Output is a table-ready CSV plus a console
summary.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scipy.stats import norm  # noqa: E402

from evalaudit.ratio import delta_log_ratio_ci, fieller_ci  # noqa: E402
from evalaudit.uplift import bootstrap_ratio_ci, match_scaled_beta  # noqa: E402

# Reported arm means (continuous Deloitte rubric), on a 0-100 scale.
M_CONTROL = 25.0    # control arm mean
M_TREAT = 63.0      # Opus-4-assisted arm mean
SPREAD = 13.0       # the card's unlabelled "±13%" on the control and Opus means
SUPPORT = 100.0     # rubric bounded on [0, 100]
ACCEPTABLE = 2.8    # threat analysis: <= 2.8x keeps risk acceptable
ASL3 = 5.0          # threat analysis: >= 5x creates significant risk
ARMS = (8, 9, 10)   # reported arm sizes

OUTFILE = Path(__file__).resolve().parents[1] / "data" / "derived" / "uplift_readings.csv"

R = M_TREAT / M_CONTROL


def _fmt(x):
    if math.isinf(x):
        return "+inf" if x > 0 else "-inf"
    if math.isnan(x):
        return "n/a"
    return f"{x:.2f}"


def verdict(low, high):
    """Human-readable verdict for a (possibly unbounded) ratio interval."""
    parts = []
    parts.append(
        f"straddles {ACCEPTABLE}x" if low <= ACCEPTABLE <= high else f"resolves vs {ACCEPTABLE}x"
    )
    if low <= 1.0 <= high:
        parts.append("includes 1x (no uplift)")
    if high >= ASL3:
        parts.append(f"reaches {ASL3}x")
    return "; ".join(parts)


# Each reading maps the "±13%" to an arm-mean standard error.
#   SD:            it is a participant-level SD, so SE = SD / sqrt(n)  (n-dependent)
#   SE:            it is the SE of the mean directly                  (n-free)
#   CI half-width: it is a 95%-CI half-width, so SE = 13 / 1.96       (n-free)
# A pooled/model-based-SE reading coincides numerically with the SE reading for
# this ratio (both arms carry the same 13), so it is not a separate row.
def se_for_reading(reading, n):
    if reading == "SD":
        return SPREAD / math.sqrt(n)
    if reading == "SE":
        return SPREAD
    if reading == "CI half-width":
        return SPREAD / 1.96
    raise ValueError(reading)


def sd_for_bootstrap(reading, n):
    """Participant-level SD implied by a reading, for the scaled-Beta bootstrap."""
    se = se_for_reading(reading, n)
    return se * math.sqrt(n)  # SD = SE * sqrt(n)


def main():
    rows = []
    print("Opus 4 bio-uplift trial — resolving-power reconstruction (ratio of means)")
    print(f"reported arm AVERAGES: control {M_CONTROL:.0f}%, Opus 4 {M_TREAT:.0f}%; "
          f"uplift = {R:.2f}x  (card: 2.53x, from unrounded means)")
    print(f"threat-analysis thresholds: acceptable <= {ACCEPTABLE}x, "
          f"significant-risk >= {ASL3}x")
    print("the card attaches an UNLABELLED '±13%' to the means; we enumerate every "
          "admissible reading.\n")

    # SD reading is swept over arm sizes; the n-free readings are reported once
    # (with the bootstrap evaluated at the middle arm size, n=9).
    plan = (
        [("SD", n) for n in ARMS]
        + [("SE", None), ("CI half-width", None)]
    )

    for reading, n in plan:
        n_boot_arm = n if n is not None else 9
        se = se_for_reading(reading, n_boot_arm)
        sd = sd_for_bootstrap(reading, n_boot_arm)

        # Fieller (headline), z and -- where n is explicit -- t(df = n-1).
        fz = fieller_ci(M_TREAT, se, M_CONTROL, se, alpha=0.05, df=None)
        df = (n - 1) if n is not None else None
        ft = fieller_ci(M_TREAT, se, M_CONTROL, se, alpha=0.05, df=df) if df else None
        # Delta method (check).
        _, dlo, dhi = delta_log_ratio_ci(M_TREAT, se, M_CONTROL, se, alpha=0.05)
        # Parametric bootstrap on scaled-Beta arms.
        _, blo, bhi, feasible = bootstrap_ratio_ci(
            M_TREAT, sd, n_boot_arm, M_CONTROL, sd, n_boot_arm,
            support=SUPPORT, alpha=0.05, n_boot=20000, seed=0,
        )
        match_ctrl = match_scaled_beta(M_CONTROL, sd, SUPPORT)

        arm_label = f"{n}" if n is not None else "n-free"
        print(f"Reading = {reading!r}  (arm {arm_label}, SE={se:.2f}, "
              f"implied participant SD={sd:.1f}):")
        print(f"  Fieller (z):   {_fmt(fz.low)}x – {_fmt(fz.high)}x  [{fz.kind}, "
              f"g={fz.g:.3f}]  -> {verdict(fz.low, fz.high)}")
        if ft is not None:
            print(f"  Fieller (t{df}): {_fmt(ft.low)}x – {_fmt(ft.high)}x  [{ft.kind}]")
        print(f"  delta (check): {_fmt(dlo)}x – {_fmt(dhi)}x  -> {verdict(dlo, dhi)}")
        if feasible:
            print(f"  bootstrap:     {_fmt(blo)}x – {_fmt(bhi)}x")
        else:
            print(f"  bootstrap:     INFEASIBLE — participant SD {sd:.1f} exceeds the "
                  f"Bhatia–Davis bound for a {M_CONTROL:.0f}% mean on [0,100]")
        print()

        def emit(method, lo, hi, kind, extra=""):
            rows.append({
                "reading": reading,
                "arm_n": arm_label,
                "se": round(se, 4),
                "implied_participant_sd": round(sd, 2),
                "method": method,
                "ratio": round(R, 4),
                "low": _fmt(lo),
                "high": _fmt(hi),
                "kind": kind,
                "straddles_2.8x": lo <= ACCEPTABLE <= hi,
                "reaches_5x": hi >= ASL3,
                "includes_1x": lo <= 1.0 <= hi,
                "note": extra,
            })

        emit("fieller_z", fz.low, fz.high, fz.kind, f"g={fz.g:.3f}")
        if ft is not None:
            emit("fieller_t", ft.low, ft.high, ft.kind, f"df={df}")
        emit("delta_z", dlo, dhi, "bounded")
        if feasible:
            emit("bootstrap", blo, bhi, "bounded")
        else:
            emit("bootstrap", float("nan"), float("nan"), "infeasible",
                 f"participant SD {sd:.1f} > Bhatia-Davis bound "
                 f"{match_ctrl.support * math.sqrt((M_CONTROL/SUPPORT)*(1-M_CONTROL/SUPPORT)):.1f}")

    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTFILE.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Significance of the uplift itself (magnitude question, not existence).
    se_sd = SPREAD / math.sqrt(9)
    z_sd = (M_TREAT - M_CONTROL) / math.sqrt(2) / se_sd
    z_se = (M_TREAT - M_CONTROL) / math.sqrt(2) / SPREAD
    p_se = 2 * (1 - norm.cdf(abs(z_se)))
    print("Takeaway: EVERY admissible reading straddles the 2.8x acceptable line — the")
    print("binding threshold, since 2.53x sits just below it. Under the SE reading the")
    print("Fieller set is UNBOUNDED ABOVE (the control mean is not significant at 95%:")
    print("25/13 ≈ 1.92 < 1.96), so the delta interval that the card's numbers would")
    print("otherwise imply is a linearisation artifact. Uplift-vs-control is significant")
    print(f"under the SD reading (z≈{z_sd:.0f}) and marginal under the SE reading "
          f"(p≈{p_se:.2f}); the failure is one of locating MAGNITUDE, not existence.")

    # ---- Resolving power: how far short the trial falls (SD reading, t). --- #
    # Smallest per-arm n at which the SD-reading Fieller upper bound clears 2.8x,
    # and, at the sizes used, the largest point uplift that would resolve below it.
    def sd_upper(n_arm):
        se_n = SPREAD / math.sqrt(n_arm)
        return fieller_ci(M_TREAT, se_n, M_CONTROL, se_n, alpha=0.05, df=n_arm - 1).high
    n_resolve = next((k for k in range(ARMS[0], 5000) if sd_upper(k) < ACCEPTABLE), None)
    se8 = SPREAD / math.sqrt(ARMS[0])
    mt = M_TREAT
    while (mt > M_CONTROL and
           fieller_ci(mt, se8, M_CONTROL, se8, alpha=0.05, df=ARMS[0] - 1).high >= ACCEPTABLE):
        mt -= 0.05
    print(f"\nResolving power (SD reading, small-sample t): the {ACCEPTABLE}x line is")
    print(f"  resolved only at n >= {n_resolve} per arm (vs the {ARMS[0]}-{ARMS[-1]} used);")
    print(f"  at n={ARMS[0]}, only a point uplift <= {mt / M_CONTROL:.2f}x "
          f"(treatment mean <= {mt:.0f}%) would resolve below {ACCEPTABLE}x.")

    # ---- Correlation robustness: does a paired design flip the verdict? ---- #
    se9 = SPREAD / math.sqrt(9)
    print(f"Correlation robustness (SD reading, n=9): SD-Fieller upper bound vs "
          f"between-arm correlation rho (cov = rho*se^2):")
    for rho in (0.0, 0.3, 0.5, 0.7, 0.9, 1.0):
        f = fieller_ci(M_TREAT, se9, M_CONTROL, se9, alpha=0.05, df=8, cov=rho * se9 * se9)
        flag = "" if f.high >= ACCEPTABLE else "  <-- resolves below 2.8x"
        print(f"  rho={rho:.1f}: upper bound {f.high:.2f}x{flag}")

    print(f"\nwrote {OUTFILE.relative_to(Path.cwd()) if OUTFILE.is_relative_to(Path.cwd()) else OUTFILE}")


if __name__ == "__main__":
    main()
