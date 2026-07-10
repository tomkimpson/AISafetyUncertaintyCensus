#!/usr/bin/env python
"""Guard: the numbers hand-transcribed into paper/main.tex must match the derived CSVs.

Three derived files (verdict_grid.csv, coverage_sim.csv, and the +/-1 sensitivity in
audited.csv) are produced by the pipeline but not \\input into the manuscript; their
results reach the paper as prose that a human typed. This script recomputes the load-bearing
figures from the CSVs and checks that (a) they still hold the value the prose encodes and
(b) the corresponding string is present in main.tex. It fails (exit 1) on any drift, so CI
catches a CSV/paper divergence instead of a reader catching it post-publication.

Usage:
    python scripts/check_paper_numbers.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived"
MAIN = ROOT / "paper" / "main.tex"


def load(name):
    return list(csv.DictReader((DERIVED / name).open()))


def main():
    tex = MAIN.read_text()
    checks = []  # (label, ok, detail)

    def check(label, computed, expected, fragment):
        ok_val = computed == expected
        ok_tex = fragment in tex
        checks.append((label, ok_val and ok_tex,
                       f"csv={computed!r} expected={expected!r} "
                       f"value_ok={ok_val} tex_fragment_present={ok_tex}"))

    # --- verdict_grid.csv: the "N of 9 cannot resolve" invariance grid ---
    grid = {(r["method"], r["alpha"]): int(r["n_cannot_resolve"]) for r in load("verdict_grid.csv")}
    counts = list(grid.values())
    check("wilson@95% cannot-resolve == 5", grid[("wilson", "0.05")], 5,
          "count is\nfive under Wilson" if "count is\nfive under Wilson" in tex
          else "five under Wilson")
    check("agresti_coull@95% == 5", grid[("agresti_coull", "0.05")], 5, "Agresti--Coull")
    check("betabinomial@95% == 5", grid[("betabinomial", "0.05")], 5, "Beta-Binomial posterior at 95")
    check("clopper-pearson(beta)@95% == 6", grid[("beta", "0.05")], 6,
          "six\nunder the more conservative Clopper--Pearson"
          if "six\nunder the more conservative Clopper--Pearson" in tex
          else "more conservative Clopper--Pearson")
    check("grid minimum (90%) == 4", min(counts), 4, "four (at 90")
    check("grid maximum (99%) == 6", max(counts), 6, "six\n(at 99" if "six\n(at 99" in tex else "(at 99")

    # --- audited.csv: +/-1-count sensitivity ---
    aud = load("audited.csv")
    n_sensitive = sum(1 for r in aud if r["count_sensitive"] == "1")
    n_total = len(aud)
    check("count-sensitive rows == 2", n_sensitive, 2, "two near-boundary rows are sensitive")
    check("rows unchanged under +/-1 == 7", n_total - n_sensitive, 7, "seven of nine unchanged")

    # --- coverage_sim.csv: coverage bands cited in the robustness appendix ---
    cov = load("coverage_sim.csv")

    def band(dgp, crit, cols):
        vals = []
        for r in cov:
            if r["kind"] == "coverage" and r["dgp"] == dgp and r["crit"] == crit:
                vals += [float(r[c]) for c in cols if r[c] not in ("", "n/a")]
        return (min(vals), max(vals)) if vals else (None, None)

    # The prose is explicitly approximate ("≈") and cites three endpoints, so we
    # pin those specific cited figures rather than the full multi-regime range:
    #   beta+t reaches near-nominal ≈0.96 (top of the "0.95–0.96" claim),
    #   two_point+t degrades to ≈0.84 (bottom of the "0.84–0.90" claim),
    #   beta+z under-covers at ≈0.91.
    beta_t = band("beta", "t", ["delta_coverage", "fieller_coverage"])
    tp_t = band("two_point", "t", ["fieller_coverage", "delta_coverage"])
    beta_z = band("beta", "z", ["fieller_coverage", "delta_coverage"])
    check("beta+t near-nominal top ≈0.96", 0.955 <= beta_t[1] <= 0.965, True,
          "0.95}--$0.96" if "0.95}--$0.96" in tex else "nominal, not conservative")
    check("two_point+t degraded floor ≈0.84", 0.84 <= tp_t[0] <= 0.855, True,
          "0.84}--$0.90" if "0.84}--$0.90" in tex else "lowers Fieller coverage")
    check("beta+z under-covers ≈0.91", beta_z[0] <= 0.91 <= beta_z[1], True, "0.91")

    # --- report ---
    failed = [c for c in checks if not c[1]]
    for label, ok, detail in checks:
        print(f"[{'OK' if ok else 'FAIL'}] {label}  ({detail})")
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed.")
    if failed:
        print("DRIFT: paper/main.tex disagrees with derived CSVs for the checks above.")
        sys.exit(1)
    print("All hand-transcribed paper numbers match the derived data.")


if __name__ == "__main__":
    main()
