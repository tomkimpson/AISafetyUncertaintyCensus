#!/usr/bin/env python
"""Run the eval audit over data/raw/evals.csv and write data/derived/audited.csv.

Usage:
    python scripts/run_audit.py [--alpha 0.05] [--ci-method wilson]

Each row is audited with :func:`evalaudit.audit`. Rows flagged is_illustrative=1
carry demo numbers; they exercise the pipeline until the real census lands.
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
    critical_deff,
    design_effect,
    effective_n,
    prob_above,
)
from evalaudit.intervals import proportion_ci, straddles  # noqa: E402

# Assumed items-per-cluster (m) for the ICC->DEFF translation. None => no
# item-clustering structure applies (DEFF fixed at 1). These are analysis
# assumptions, not published facts (per-cluster counts are unpublished), which
# is why they live here and not in data/raw/evals.csv. See the robustness
# appendix of the paper. critical_deff itself is m-free; only the ICC
# translation uses m.
ASSUMED_CLUSTER_SIZE = {
    "swebench_hard": 10,        # tasks cluster by repository (cf. SWE-bench Verified: 500 tasks / 12 repos)
    "bioweapons_knowledge": 5,  # 33 questions plausibly cluster by topic/protocol
    "metr_dedup": None,         # n = independent trials of ONE task; item-clustering N/A
}
DEFAULT_M = 10
ICC_GRID = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]
M_GRID = [5, 10, 20]
MILLER_DEFF = 9.0  # Miller (arXiv:2411.00640): clustered SE ~3x naive observed => DEFF ~ 9

# Grid over which the "N of 9 cannot resolve" headline count must be invariant:
# interval construction x confidence level. Beta-Binomial (uniform prior) is
# included as a Bayesian cross-check: a row "resolves" if the posterior clears
# the alpha/2 or 1-alpha/2 decision mark, else it "cannot resolve".
GRID_METHODS = ["wilson", "beta", "agresti_coull", "betabinomial"]
GRID_ALPHAS = [0.10, 0.05, 0.01]
# Run-level convention for SWE-bench: the reported mean is over 10 runs per task,
# so a run-generalisation estimand would treat the denominator as tasks x runs.
SWEBENCH_RUNS = 10


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--ci-method", default="wilson")
    ap.add_argument("--ref-icc", type=float, default=0.2,
                    help="ICC used for the clustered columns in the wide output")
    ap.add_argument("--infile", default=str(ROOT / "data/raw/evals.csv"))
    ap.add_argument("--outfile", default=str(ROOT / "data/derived/audited.csv"))
    ap.add_argument("--sweep-outfile", default=str(ROOT / "data/derived/icc_sweep.csv"))
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.infile)))
    out_fields = [
        "framework", "capability", "model", "threshold", "n", "score",
        "ci_low", "ci_high", "straddles", "power_at_observed",
        "required_n", "prob_above", "verdict", "is_illustrative", "source",
        "assumed_m", "effective_n_ref", "ci_low_clust", "ci_high_clust",
        "straddles_clust", "critical_deff", "critical_icc",
        # +/-1-count sensitivity (counts reconstructed from rounded rates carry
        # a +/-1 ambiguity at n = 29-46).
        "successes", "straddles_minus1", "straddles_plus1", "count_sensitive",
        # SWE-bench dual variance convention (run-generalisation denominator).
        "n_runs", "ci_low_runs", "ci_high_runs", "straddles_runs", "convention_sensitive",
    ]
    out = []
    sweep = []
    for r in rows:
        n = int(r["n"])
        thr = float(r["threshold"])
        res = audit(
            n=n,
            threshold=thr,
            score=float(r["score"]),
            alpha=args.alpha,
            direction=r.get("direction", "above") or "above",
            ci_method=args.ci_method,
        )

        # +/-1-count sensitivity. Reconstructed counts (int(round(score*n)))
        # carry a +/-1 ambiguity; recompute the straddle verdict at successes+/-1.
        succ = res.successes

        def _strad_at(s):
            s = max(0, min(n, s))
            return straddles(thr, proportion_ci(s, n, alpha=args.alpha, method=args.ci_method))

        strad_m1 = _strad_at(succ - 1)
        strad_p1 = _strad_at(succ + 1)
        count_sensitive = (strad_m1 != res.straddles_threshold) or (
            strad_p1 != res.straddles_threshold)

        # SWE-bench dual variance convention: the reported figure is a mean over
        # 10 runs, so a run-generalisation estimand uses n_runs = tasks x runs.
        # (Our headline estimand is task-generalisation, n = tasks; this column
        # tests whether the verdict is convention-dependent.)
        if r["capability"] == "swebench_hard":
            n_runs = n * SWEBENCH_RUNS
            s_runs = int(round(res.score * n_runs))
            ci_runs = proportion_ci(s_runs, n_runs, alpha=args.alpha, method=args.ci_method)
            strad_runs = straddles(thr, ci_runs)
            convention_sensitive = strad_runs != res.straddles_threshold
        else:
            n_runs = ""
            ci_runs = ("", "")
            strad_runs = ""
            convention_sensitive = ""

        # Clustered sensitivity: assumption-driven (per-cluster counts are
        # unpublished), computed from the same rounded p_hat as the naive CI.
        m = ASSUMED_CLUSTER_SIZE.get(r["capability"], DEFAULT_M)
        cd = critical_deff(res.score, n, thr, alpha=args.alpha, method=args.ci_method)
        if m is not None:
            deff_ref = design_effect([m], args.ref_icc)
            ci_c = clustered_ci(res.score, n, deff_ref, alpha=args.alpha, method=args.ci_method)
            n_eff_ref = effective_n(n, deff=deff_ref)
            # ICC is bounded by 1; ">1" means no clustering severity at the
            # assumed m can flip this row (the DEFF needed exceeds m).
            crit_icc = (cd - 1.0) / (m - 1.0) if cd is not None else None
            if crit_icc is not None and crit_icc > 1.0:
                crit_icc = ">1"
        else:
            ci_c = res.ci
            n_eff_ref = float(n)
            crit_icc = None

        out.append({
            "framework": r["framework"],
            "capability": r["capability"],
            "model": r["model"],
            "threshold": res.threshold,
            "n": n,
            "score": round(res.score, 4),
            "ci_low": round(res.ci[0], 4),
            "ci_high": round(res.ci[1], 4),
            "straddles": int(res.straddles_threshold),
            "power_at_observed": round(res.power_at_observed, 4),
            "required_n": res.required_n,
            "prob_above": round(res.prob_above, 4),
            "verdict": res.verdict,
            "is_illustrative": r.get("is_illustrative", ""),
            "source": r.get("source", ""),
            "assumed_m": m if m is not None else "",
            "effective_n_ref": round(n_eff_ref, 1),
            "ci_low_clust": round(ci_c[0], 4),
            "ci_high_clust": round(ci_c[1], 4),
            "straddles_clust": int(straddles(thr, ci_c)),
            "critical_deff": round(cd, 2) if cd is not None else "",
            "critical_icc": (crit_icc if isinstance(crit_icc, str)
                             else round(crit_icc, 3) if crit_icc is not None else ""),
            "successes": succ,
            "straddles_minus1": int(strad_m1),
            "straddles_plus1": int(strad_p1),
            "count_sensitive": int(count_sensitive),
            "n_runs": n_runs,
            "ci_low_runs": round(ci_runs[0], 4) if ci_runs[0] != "" else "",
            "ci_high_runs": round(ci_runs[1], 4) if ci_runs[1] != "" else "",
            "straddles_runs": int(strad_runs) if strad_runs != "" else "",
            "convention_sensitive": (int(convention_sensitive)
                                     if convention_sensitive != "" else ""),
        })

        # Long-format ICC x m sweep. Rows without a clustering structure get a
        # single DEFF=1 line so every eval appears in the sweep file.
        if m is None:
            sweep.append(_sweep_row(r, res, n, thr, "", 0.0, 1.0, float(n), res.ci))
        else:
            for m_s in M_GRID:
                for icc in ICC_GRID:
                    deff = design_effect([m_s], icc)
                    n_eff = effective_n(n, deff=deff)
                    if n_eff < 1.0:
                        continue  # ICC/m combination too severe for this n
                    ci_s = clustered_ci(res.score, n, deff, alpha=args.alpha, method=args.ci_method)
                    sweep.append(_sweep_row(r, res, n, thr, m_s, icc, deff, n_eff, ci_s))

    Path(args.outfile).parent.mkdir(parents=True, exist_ok=True)
    with open(args.outfile, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_fields)
        w.writeheader()
        w.writerows(out)

    sweep_fields = [
        "framework", "capability", "model", "n", "score", "threshold",
        "assumed_m", "icc", "deff", "effective_n", "ci_low", "ci_high",
        "straddles",
    ]
    with open(args.sweep_outfile, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=sweep_fields)
        w.writeheader()
        w.writerows(sweep)

    # Verdict-invariance grid: the "N of 9 cannot resolve" count across every
    # interval construction x confidence level. Guards against the headline
    # being an artifact of one construction or one alpha (forking-paths note).
    grid_rows = _verdict_grid(rows)
    grid_outfile = Path(args.outfile).with_name("verdict_grid.csv")
    with open(grid_outfile, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["method", "alpha", "n_cannot_resolve", "n_total"])
        w.writeheader()
        w.writerows(grid_rows)

    # Console summary.
    n_straddle = sum(o["straddles"] for o in out)
    print(f"Audited {len(out)} rows -> {args.outfile}")
    print(f"ICC sweep ({len(sweep)} rows) -> {args.sweep_outfile}")
    print(f"Verdict grid ({len(grid_rows)} cells) -> {grid_outfile}")
    print(f"{n_straddle}/{len(out)} cannot resolve their own threshold "
          f"at the {int((1-args.alpha)*100)}% level.\n")

    # Robustness call-outs for the paper prose.
    sensitive = [o for o in out if o["count_sensitive"]]
    if sensitive:
        print("±1-count sensitive rows (verdict flips at successes±1):")
        for o in sensitive:
            print(f"  {o['capability']} {o['model']}: verdict {o['verdict']} "
                  f"(straddles -1={o['straddles_minus1']}, +1={o['straddles_plus1']})")
    else:
        print("±1-count sensitivity: no verdict flips at successes±1 for any row.")
    conv = [o for o in out if o["convention_sensitive"] == 1]
    if conv:
        print("SWE-bench convention-sensitive rows (task- vs run-generalisation differ):")
        for o in conv:
            print(f"  {o['model']}: task n={o['n']} straddles={o['straddles']}; "
                  f"run n={o['n_runs']} straddles={o['straddles_runs']}")
    else:
        print("SWE-bench convention: task- and run-generalisation give the same verdict.")
    counts = {(g["method"], g["alpha"]): g["n_cannot_resolve"] for g in grid_rows}
    at_95 = {m: counts[(m, 0.05)] for m in GRID_METHODS}
    print(f"Verdict-grid invariance @95%: {at_95} (of {len(out)}); "
          f"full grid range {min(g['n_cannot_resolve'] for g in grid_rows)}"
          f"–{max(g['n_cannot_resolve'] for g in grid_rows)} across "
          f"{len(GRID_METHODS)} constructions × {len(GRID_ALPHAS)} levels.\n")
    for o in out:
        print(f"  [{o['verdict']:<22}] {o['framework']}/{o['capability']} "
              f"{o['model']}: score={o['score']} n={o['n']} "
              f"CI=({o['ci_low']},{o['ci_high']}) thr={o['threshold']} "
              f"| required_n={o['required_n']} P(>thr)={o['prob_above']}")
        print(f"      {_cluster_line(o)}")


def _verdict_grid(rows):
    """Count 'cannot resolve' rows across interval construction x confidence level.

    For frequentist methods a row cannot resolve if its CI straddles the
    threshold. For the Beta-Binomial (uniform-prior) posterior, a row resolves
    only if P(rate > thr) clears the alpha/2 or 1-alpha/2 decision mark; else it
    cannot resolve. Returns one dict per (method, alpha) cell.
    """
    grid = []
    for method in GRID_METHODS:
        for alpha in GRID_ALPHAS:
            n_cannot = 0
            for r in rows:
                n = int(r["n"])
                thr = float(r["threshold"])
                succ = int(round(float(r["score"]) * n))
                if method == "betabinomial":
                    p = prob_above(thr, succ, n, prior=(1.0, 1.0))
                    resolves = (p >= 1 - alpha / 2) or (p <= alpha / 2)
                    cannot = not resolves
                else:
                    ci = proportion_ci(succ, n, alpha=alpha, method=method)
                    cannot = straddles(thr, ci)
                n_cannot += int(cannot)
            grid.append({
                "method": method, "alpha": alpha,
                "n_cannot_resolve": n_cannot, "n_total": len(rows),
            })
    return grid


def _sweep_row(r, res, n, thr, m, icc, deff, n_eff, ci):
    return {
        "framework": r["framework"],
        "capability": r["capability"],
        "model": r["model"],
        "n": n,
        "score": round(res.score, 4),
        "threshold": thr,
        "assumed_m": m,
        "icc": icc,
        "deff": round(deff, 3),
        "effective_n": round(n_eff, 1),
        "ci_low": round(ci[0], 4),
        "ci_high": round(ci[1], 4),
        "straddles": int(straddles(thr, ci)),
    }


def _cluster_line(o):
    """One-line clustered-sensitivity summary for the console."""
    if o["straddles"]:
        return "already straddles at DEFF=1 (no clustering needed)"
    if o["critical_deff"] == "":
        return "never flips for any DEFF <= n"
    cd = float(o["critical_deff"])
    if o["assumed_m"] == "":
        icc_part = "(single-task trials; ICC translation n/a)"
    else:
        icc_part = f"(ICC~{o['critical_icc']} @ m={o['assumed_m']})"
    miller = "inside" if cd < MILLER_DEFF else "beyond"
    return (f"flips at DEFF={cd} {icc_part} — {miller} Miller's observed "
            f"{MILLER_DEFF:.0f}x range")


if __name__ == "__main__":
    main()
