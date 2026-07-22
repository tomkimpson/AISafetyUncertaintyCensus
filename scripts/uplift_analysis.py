#!/usr/bin/env python
"""Reconstruct uncertainty for the Opus 4 bio-uplift ratio.

The card reports continuous-rubric arm means of 25% and 63%, attaches an
unlabelled ``±13%`` to both, and says each arm contained 8--10 participants.
We evaluate three conventional readings of that dispersion. For the SD reading
we enumerate all nine ordered (control, treatment) arm-size combinations and
use Welch--Satterthwaite degrees of freedom. Fieller sets are computed on the
whole real line; because both target means are nonnegative, the table also
reports their explicitly restricted intersection with the nonnegative-ratio
parameter space.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from evalaudit.ratio import FiellerResult, delta_log_ratio_ci, fieller_ci  # noqa: E402
from evalaudit.uplift import bootstrap_ratio_ci, match_scaled_beta  # noqa: E402

M_CONTROL = 25.0
M_TREAT = 63.0
SPREAD = 13.0
SUPPORT = 100.0
ACCEPTABLE = 2.8
ASL3 = 5.0
ARMS = (8, 9, 10)
OUTFILE = ROOT / "data" / "derived" / "uplift_readings.csv"
RATIO = M_TREAT / M_CONTROL


def _fmt(value):
    if math.isinf(value):
        return "+inf" if value > 0 else "-inf"
    if math.isnan(value):
        return "n/a"
    return f"{value:.2f}"


def _set_string(result: FiellerResult) -> str:
    if not result.components:
        return "empty"
    return " U ".join(f"[{_fmt(low)}, {_fmt(high)}]" for low, high in result.components)


def welch_df(se_treat, se_control, n_treat, n_control):
    """Welch--Satterthwaite df from the two estimated arm-mean variances."""
    numerator = (se_treat**2 + se_control**2) ** 2
    denominator = (
        se_treat**4 / (n_treat - 1)
        + se_control**4 / (n_control - 1)
    )
    return numerator / denominator


def reading_standard_errors(reading, n_control=None, n_treat=None):
    if reading == "SD":
        return SPREAD / math.sqrt(n_control), SPREAD / math.sqrt(n_treat)
    if reading == "SE":
        return SPREAD, SPREAD
    if reading == "CI half-width":
        return SPREAD / 1.96, SPREAD / 1.96
    raise ValueError(reading)


def _verdict(low, high):
    parts = [
        f"straddles {ACCEPTABLE}x"
        if low <= ACCEPTABLE <= high
        else f"resolves vs {ACCEPTABLE}x"
    ]
    if low <= 1.0 <= high:
        parts.append("includes 1x")
    if high >= ASL3:
        parts.append(f"reaches {ASL3}x")
    return "; ".join(parts)


def main():
    rows = []
    print("Opus 4 bio-uplift trial — ratio-of-means reconstruction")
    print(
        f"reported means: control={M_CONTROL:.0f}%, Opus 4={M_TREAT:.0f}%, "
        f"ratio={RATIO:.2f}x (card: 2.53x from unrounded means)"
    )
    print("three conventional readings of the unlabelled ±13%; not an exhaustive list\n")

    plan = [
        ("SD", n_control, n_treat)
        for n_control in ARMS
        for n_treat in ARMS
    ] + [("SE", None, None), ("CI half-width", None, None)]

    for reading, n_control, n_treat in plan:
        se_control, se_treat = reading_standard_errors(
            reading, n_control=n_control, n_treat=n_treat
        )
        if reading == "SD":
            df = welch_df(se_treat, se_control, n_treat, n_control)
            arm_label = f"{n_control}/{n_treat}"
            sd_control = sd_treat = SPREAD
        else:
            df = None
            arm_label = "n-free"
            # A participant-level bootstrap is not identified without arm sizes
            # when the published dispersion is an SE or interval half-width.
            sd_control = sd_treat = None

        fieller_real = fieller_ci(
            M_TREAT, se_treat, M_CONTROL, se_control, alpha=0.05, df=df
        )
        fieller_positive = fieller_real.restrict_nonnegative()
        _, delta_low, delta_high = delta_log_ratio_ci(
            M_TREAT, se_treat, M_CONTROL, se_control, alpha=0.05, df=df
        )

        if reading == "SD":
            _, boot_low, boot_high, feasible = bootstrap_ratio_ci(
                M_TREAT, sd_treat, n_treat,
                M_CONTROL, sd_control, n_control,
                support=SUPPORT, alpha=0.05, n_boot=20000, seed=0,
            )
        else:
            boot_low = boot_high = float("nan")
            feasible = False

        low, high = fieller_positive.low, fieller_positive.high
        print(
            f"{reading:13s} arms {arm_label:6s}: Fieller real set "
            f"{_set_string(fieller_real)}; nonnegative {_set_string(fieller_positive)}"
        )

        common = {
            "reading": reading,
            "arm_n": arm_label,
            "n_control": n_control if n_control is not None else "",
            "n_treat": n_treat if n_treat is not None else "",
            "df": round(df, 3) if df is not None else "",
            "se_control": round(se_control, 4),
            "se_treat": round(se_treat, 4),
            "ratio": round(RATIO, 4),
        }

        def emit(method, lo, hi, kind, real_set="", nonnegative_set="", note=""):
            rows.append({
                **common,
                "method": method,
                "low": _fmt(lo),
                "high": _fmt(hi),
                "kind": kind,
                "real_set": real_set,
                "nonnegative_set": nonnegative_set,
                "straddles_2.8x": lo <= ACCEPTABLE <= hi,
                "reaches_5x": hi >= ASL3,
                "includes_1x": lo <= 1.0 <= hi,
                "note": note,
            })

        emit(
            "fieller_t" if df is not None else "fieller_z",
            low,
            high,
            fieller_positive.kind,
            _set_string(fieller_real),
            _set_string(fieller_positive),
            (
                f"Welch-Satterthwaite df={df:.3f}; " if df is not None else "normal critical value; "
            ) + f"g={fieller_real.g:.3f}; displayed set restricted to ratio >= 0",
        )
        emit("delta_t" if df is not None else "delta_z", delta_low, delta_high, "bounded")
        if feasible:
            emit("bootstrap", boot_low, boot_high, "bounded")
        else:
            emit(
                "bootstrap", float("nan"), float("nan"), "not_identified",
                note="participant-level dispersion is not identified without arm sizes",
            )

    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTFILE.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    sd_fieller = [
        row for row in rows
        if row["reading"] == "SD" and row["method"] == "fieller_t"
    ]
    assert len(sd_fieller) == 9
    assert all(row["straddles_2.8x"] for row in sd_fieller)
    assert all(
        row["straddles_2.8x"]
        for row in rows
        if row["method"] in {"fieller_t", "fieller_z"}
    )
    print("\nAll nine SD arm-size combinations and both n-free readings retain 2.8x.")
    print("The SE reading's whole-real-line set is disjoint; only its explicit")
    print("intersection with the nonnegative-ratio parameter space is one positive ray.")

    def sd_upper(n_arm):
        se = SPREAD / math.sqrt(n_arm)
        df = welch_df(se, se, n_arm, n_arm)
        return fieller_ci(
            M_TREAT, se, M_CONTROL, se, alpha=0.05, df=df
        ).restrict_nonnegative().high

    n_resolve = next((n for n in range(8, 5000) if sd_upper(n) < ACCEPTABLE), None)
    print(
        f"Equal-arm SD illustration: the upper bound falls below {ACCEPTABLE}x "
        f"at n={n_resolve} per arm."
    )

    se9 = SPREAD / math.sqrt(9)
    df9 = welch_df(se9, se9, 9, 9)
    print("Correlation sensitivity (SD reading, equal n=9):")
    for rho in (0.0, 0.3, 0.5, 0.7, 0.9, 1.0):
        result = fieller_ci(
            M_TREAT, se9, M_CONTROL, se9, alpha=0.05, df=df9,
            cov=rho * se9 * se9,
        ).restrict_nonnegative()
        flag = "" if result.high >= ACCEPTABLE else " (resolves below 2.8x)"
        print(f"  rho={rho:.1f}: upper={result.high:.2f}x{flag}")

    control_match = match_scaled_beta(M_CONTROL, SPREAD, SUPPORT)
    assert control_match.feasible
    print(f"\nwrote {OUTFILE}")


if __name__ == "__main__":
    main()
