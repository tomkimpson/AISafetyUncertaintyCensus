#!/usr/bin/env python
"""Run the model-level threshold audit and its declared sensitivities.

The primary frequentist decision uses a one-sided 95% Wilson bound in the
observed direction.  A central two-sided 95% Wilson interval, the SWE-bench
run-level convention, reconstructed-count perturbations, and an assumption
grid for item clustering are retained as sensitivity analyses.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from evalaudit import (  # noqa: E402
    audit,
    clustered_ci,
    clustered_directional_bounds,
    critical_deff,
    design_effect,
    effective_n,
    prob_above,
)
from evalaudit.intervals import (  # noqa: E402
    proportion_ci,
    proportion_directional_bounds,
    straddles,
)

# These are analysis assumptions because the source cards do not publish the
# required cluster labels. METR rows are repeated trials of one fixed task, so
# an item-clustering translation is not applicable.
ASSUMED_CLUSTER_SIZE = {
    "swebench_hard": 10,
    "bioweapons_knowledge": 5,
    "metr_dedup": None,
}
DEFAULT_M = 10
ICC_GRID = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]
M_GRID = [5, 10, 20]
GRID_METHODS = ["wilson", "beta", "agresti_coull", "beta_posterior"]
GRID_ALPHAS = [0.10, 0.05, 0.01]
SWEBENCH_RUNS = 10


def _bounds_at(successes, n, alpha, method):
    return (
        proportion_directional_bounds(successes, n, alpha=alpha, method=method),
        proportion_ci(successes, n, alpha=alpha, method=method),
    )


def _critical_icc(critical, m):
    if critical in (None, ""):
        return ""
    value = (float(critical) - 1.0) / (m - 1.0)
    return ">1" if value > 1.0 else round(value, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--ci-method", default="wilson")
    ap.add_argument("--ref-icc", type=float, default=0.2)
    ap.add_argument("--infile", default=str(ROOT / "data/raw/evals.csv"))
    ap.add_argument("--outfile", default=str(ROOT / "data/derived/audited.csv"))
    ap.add_argument("--sweep-outfile", default=str(ROOT / "data/derived/icc_sweep.csv"))
    args = ap.parse_args()

    with open(args.infile) as f:
        rows = list(csv.DictReader(f))

    out_fields = [
        "record_id", "framework", "capability", "model", "threshold", "n",
        "successes", "score", "directional_low", "directional_high",
        "unresolved_primary", "two_sided_low", "two_sided_high",
        "unresolved_two_sided", "power_at_observed", "required_n",
        "prob_above", "verdict", "is_illustrative", "source",
        "assumed_m", "effective_n_ref", "directional_low_clust",
        "directional_high_clust", "unresolved_clust", "critical_deff",
        "critical_icc_m5", "critical_icc_m10", "critical_icc_m20",
        "unresolved_minus1", "unresolved_plus1", "count_sensitive",
        "n_runs", "directional_low_runs", "directional_high_runs",
        "unresolved_runs", "two_sided_low_runs", "two_sided_high_runs",
        "unresolved_two_sided_runs", "convention_sensitive",
        # Compatibility aliases: these are the primary directional bounds.
        "ci_low", "ci_high", "straddles",
    ]
    out = []
    sweep = []

    for row in rows:
        n = int(row["n"])
        threshold = float(row["threshold"])
        result = audit(
            n=n,
            threshold=threshold,
            score=float(row["score"]),
            alpha=args.alpha,
            direction=row.get("direction", "above") or "above",
            ci_method=args.ci_method,
        )

        successes = result.successes

        def unresolved_at(s):
            s = max(0, min(n, s))
            bounds = proportion_directional_bounds(
                s, n, alpha=args.alpha, method=args.ci_method
            )
            return straddles(threshold, bounds)

        unresolved_minus1 = unresolved_at(successes - 1)
        unresolved_plus1 = unresolved_at(successes + 1)
        count_sensitive = (
            unresolved_minus1 != result.unresolved_directional
            or unresolved_plus1 != result.unresolved_directional
        )

        if row["capability"] == "swebench_hard":
            n_runs = n * SWEBENCH_RUNS
            successes_runs = int(round(result.score * n_runs))
            directional_runs, two_sided_runs = _bounds_at(
                successes_runs, n_runs, args.alpha, args.ci_method
            )
            unresolved_runs = straddles(threshold, directional_runs)
            unresolved_two_sided_runs = straddles(threshold, two_sided_runs)
            convention_sensitive = unresolved_runs != result.unresolved_directional
        else:
            n_runs = ""
            directional_runs = ("", "")
            two_sided_runs = ("", "")
            unresolved_runs = ""
            unresolved_two_sided_runs = ""
            convention_sensitive = ""

        m = ASSUMED_CLUSTER_SIZE.get(row["capability"], DEFAULT_M)
        if m is None:
            deff_ref = 1.0
            effective_ref = float(n)
            clustered_bounds = result.directional_bounds
            critical = None
        else:
            deff_ref = design_effect([m], args.ref_icc)
            effective_ref = effective_n(n, deff=deff_ref)
            clustered_bounds = clustered_directional_bounds(
                result.score, n, deff_ref, alpha=args.alpha, method=args.ci_method
            )
            critical = critical_deff(
                result.score, n, threshold, alpha=args.alpha,
                method=args.ci_method, directional=True,
            )

        record = {
            "record_id": row["record_id"],
            "framework": row["framework"],
            "capability": row["capability"],
            "model": row["model"],
            "threshold": result.threshold,
            "n": n,
            "successes": successes,
            "score": round(result.score, 4),
            "directional_low": round(result.directional_bounds[0], 4),
            "directional_high": round(result.directional_bounds[1], 4),
            "unresolved_primary": int(result.unresolved_directional),
            "two_sided_low": round(result.two_sided_ci[0], 4),
            "two_sided_high": round(result.two_sided_ci[1], 4),
            "unresolved_two_sided": int(result.unresolved_two_sided),
            "power_at_observed": round(result.power_at_observed, 4),
            "required_n": result.required_n,
            "prob_above": round(result.prob_above, 4),
            "verdict": result.verdict,
            "is_illustrative": row.get("is_illustrative", ""),
            "source": row.get("source", ""),
            "assumed_m": m if m is not None else "",
            "effective_n_ref": round(effective_ref, 1),
            "directional_low_clust": round(clustered_bounds[0], 4),
            "directional_high_clust": round(clustered_bounds[1], 4),
            "unresolved_clust": int(straddles(threshold, clustered_bounds)),
            "critical_deff": round(critical, 2) if critical is not None else "",
            "critical_icc_m5": _critical_icc(critical, 5),
            "critical_icc_m10": _critical_icc(critical, 10),
            "critical_icc_m20": _critical_icc(critical, 20),
            "unresolved_minus1": int(unresolved_minus1),
            "unresolved_plus1": int(unresolved_plus1),
            "count_sensitive": int(count_sensitive),
            "n_runs": n_runs,
            "directional_low_runs": _rounded(directional_runs[0]),
            "directional_high_runs": _rounded(directional_runs[1]),
            "unresolved_runs": _int_or_blank(unresolved_runs),
            "two_sided_low_runs": _rounded(two_sided_runs[0]),
            "two_sided_high_runs": _rounded(two_sided_runs[1]),
            "unresolved_two_sided_runs": _int_or_blank(unresolved_two_sided_runs),
            "convention_sensitive": _int_or_blank(convention_sensitive),
            "ci_low": round(result.directional_bounds[0], 4),
            "ci_high": round(result.directional_bounds[1], 4),
            "straddles": int(result.unresolved_directional),
        }
        out.append(record)

        if m is None:
            sweep.append(_sweep_row(row, result, n, threshold, "", 0.0, 1.0, n))
        else:
            for m_sweep in M_GRID:
                for icc in ICC_GRID:
                    deff = design_effect([m_sweep], icc)
                    n_eff = effective_n(n, deff=deff)
                    if n_eff >= 1.0:
                        sweep.append(
                            _sweep_row(row, result, n, threshold, m_sweep, icc, deff, n_eff)
                        )

    Path(args.outfile).parent.mkdir(parents=True, exist_ok=True)
    with open(args.outfile, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(out)

    sweep_fields = [
        "record_id", "framework", "capability", "model", "n", "score",
        "threshold", "assumed_m", "icc", "deff", "effective_n",
        "directional_low", "directional_high", "unresolved_primary",
        "two_sided_low", "two_sided_high", "unresolved_two_sided",
    ]
    with open(args.sweep_outfile, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sweep_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sweep)

    grid_rows = _verdict_grid(rows)
    grid_outfile = Path(args.outfile).with_name("verdict_grid.csv")
    with open(grid_outfile, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["analysis", "method", "alpha", "n_cannot_resolve", "n_total"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(grid_rows)

    direct = [r for r in out if r["capability"] != "swebench_hard"]
    swe = [r for r in out if r["capability"] == "swebench_hard"]
    print(f"Audited {len(out)} model-level rows -> {args.outfile}")
    print(
        "Primary one-sided 95% unresolved: "
        f"direct-count {sum(r['unresolved_primary'] for r in direct)}/{len(direct)}; "
        f"SWE task-level {sum(r['unresolved_primary'] for r in swe)}/{len(swe)}; "
        f"SWE run-level {sum(r['unresolved_runs'] for r in swe)}/{len(swe)}."
    )
    print(
        "Two-sided 95% sensitivity unresolved: "
        f"task-level {sum(r['unresolved_two_sided'] for r in out)}/{len(out)}; "
        f"SWE run-level {sum(r['unresolved_two_sided_runs'] for r in swe)}/{len(swe)}."
    )
    print(f"ICC sweep ({len(sweep)} rows) -> {args.sweep_outfile}")
    print(f"Verdict grid ({len(grid_rows)} cells) -> {grid_outfile}")


def _rounded(value):
    return "" if value == "" else round(value, 4)


def _int_or_blank(value):
    return "" if value == "" else int(value)


def _sweep_row(row, result, n, threshold, m, icc, deff, n_eff):
    directional = clustered_directional_bounds(
        result.score, n, deff, alpha=result.alpha, method=result.ci_method
    )
    two_sided = clustered_ci(
        result.score, n, deff, alpha=result.alpha, method=result.ci_method
    )
    return {
        "record_id": row["record_id"],
        "framework": row["framework"],
        "capability": row["capability"],
        "model": row["model"],
        "n": n,
        "score": round(result.score, 4),
        "threshold": threshold,
        "assumed_m": m,
        "icc": icc,
        "deff": round(deff, 3),
        "effective_n": round(n_eff, 1),
        "directional_low": round(directional[0], 4),
        "directional_high": round(directional[1], 4),
        "unresolved_primary": int(straddles(threshold, directional)),
        "two_sided_low": round(two_sided[0], 4),
        "two_sided_high": round(two_sided[1], 4),
        "unresolved_two_sided": int(straddles(threshold, two_sided)),
    }


def _verdict_grid(rows):
    """Sensitivity grid for the one-sided primary and two-sided comparison."""
    grid = []
    for analysis in ("one_sided", "two_sided"):
        for method in GRID_METHODS:
            for alpha in GRID_ALPHAS:
                n_cannot = 0
                for row in rows:
                    n = int(row["n"])
                    threshold = float(row["threshold"])
                    successes = int(round(float(row["score"]) * n))
                    if method == "beta_posterior":
                        p = prob_above(threshold, successes, n, prior=(1.0, 1.0))
                        tail = alpha if analysis == "one_sided" else alpha / 2.0
                        cannot = not (p >= 1.0 - tail or p <= tail)
                    elif analysis == "one_sided":
                        bounds = proportion_directional_bounds(
                            successes, n, alpha=alpha, method=method
                        )
                        cannot = straddles(threshold, bounds)
                    else:
                        interval = proportion_ci(successes, n, alpha=alpha, method=method)
                        cannot = straddles(threshold, interval)
                    n_cannot += int(cannot)
                grid.append({
                    "analysis": analysis,
                    "method": method,
                    "alpha": alpha,
                    "n_cannot_resolve": n_cannot,
                    "n_total": len(rows),
                })
    return grid


if __name__ == "__main__":
    main()
