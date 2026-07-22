#!/usr/bin/env python
"""Fail if load-bearing derived results drift from paper/main.tex."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived"
MAIN = ROOT / "paper" / "main.tex"


def load(name):
    with (DERIVED / name).open() as f:
        return list(csv.DictReader(f))


def main():
    tex = MAIN.read_text()
    checks = []

    def check(label, condition, fragment):
        checks.append((label, bool(condition) and fragment in tex, f"fragment={fragment!r}"))

    audited = load("audited.csv")
    direct = [r for r in audited if r["capability"] != "swebench_hard"]
    swe = [r for r in audited if r["capability"] == "swebench_hard"]
    check("ten model-level audit rows", len(audited) == 10, "Ten model-level")
    check(
        "primary direct tier 2/6",
        sum(int(r["unresolved_primary"]) for r in direct) == 2 and len(direct) == 6,
        "two of six direct-count",
    )
    check(
        "primary SWE task tier 2/4",
        sum(int(r["unresolved_primary"]) for r in swe) == 2 and len(swe) == 4,
        "two of four",
    )
    check(
        "primary SWE run tier 1/4",
        sum(int(r["unresolved_runs"]) for r in swe) == 1,
        "one of four",
    )
    check(
        "two-sided task sensitivity 5/10",
        sum(int(r["unresolved_two_sided"]) for r in audited) == 5,
        "five of ten",
    )
    check(
        "two-sided mixed run sensitivity 3/10",
        sum(int(r["unresolved_two_sided"]) for r in direct)
        + sum(int(r["unresolved_two_sided_runs"]) for r in swe)
        == 3,
        "three of ten",
    )
    check(
        "one count-sensitive row",
        sum(int(r["count_sensitive"]) for r in audited) == 1,
        "only for\nSWE-bench Sonnet~4",
    )

    grid = {
        (r["analysis"], r["method"], r["alpha"]): int(r["n_cannot_resolve"])
        for r in load("verdict_grid.csv")
    }
    check(
        "one-sided Wilson 95 is 4/10",
        grid[("one_sided", "wilson", "0.05")] == 4,
        "four of ten task-level rows unresolved",
    )
    check(
        "two-sided Wilson 95 is 5/10",
        grid[("two_sided", "wilson", "0.05")] == 5,
        "central two-sided 95",
    )
    check(
        "two-sided exact 95 is 6/10",
        grid[("two_sided", "beta", "0.05")] == 6,
        "six under\nClopper--Pearson",
    )

    uplift = load("uplift_readings.csv")
    fieller = [r for r in uplift if r["method"] in {"fieller_t", "fieller_z"}]
    sd_fieller = [r for r in fieller if r["reading"] == "SD"]
    check(
        "all nine SD arm combinations present",
        len(sd_fieller) == 9
        and {(r["n_control"], r["n_treat"]) for r in sd_fieller}
        == {(str(i), str(j)) for i in (8, 9, 10) for j in (8, 9, 10)},
        "every ordered $(n_C,n_T)",
    )
    check(
        "all Fieller sets retain 2.8x",
        len(fieller) == 11 and all(r["straddles_2.8x"] == "True" for r in fieller),
        "every reading considered retains $2.8\\times$",
    )
    se_row = next(r for r in fieller if r["reading"] == "SE")
    check(
        "SE real-line Fieller set is disjoint",
        "-131.18" in se_row["real_set"] and "-inf" in se_row["real_set"],
        "$(-\\infty,-131.18]\\cup[1.05,\\infty)$",
    )

    corpus = list(csv.DictReader((ROOT / "data/raw/census_records.csv").open()))
    included = [r for r in corpus if r["include_primary"].lower() == "true"]
    check("corpus primary n=96", len(included) == 96, "\\CensusTotal{} eligible")
    check(
        "corpus no-uncertainty n=81",
        sum(r["uncertainty_class"] == "none" for r in included) == 81,
        "\\CensusNoUncertainty{} records give none",
    )
    signoff = list(
        csv.DictReader((ROOT / "data/verification/human_signoff.csv").open())
    )
    check(
        "human sign-off sheet covers eligible IDs and remains pending",
        {r["record_id"] for r in signoff} == {r["record_id"] for r in included}
        and len(signoff) == len(included)
        and all(r["human_status"] == "pending" for r in signoff),
        "sheet remains marked ``pending''",
    )

    coverage = load("coverage_sim.csv")
    sd_beta_t = [
        r for r in coverage
        if r["kind"] == "coverage" and r["reading"] == "SD"
        and r["dgp"] == "beta" and r["crit"] == "t"
    ]
    values = [float(r["fieller_coverage"]) for r in sd_beta_t]
    check(
        "Welch SD smooth-beta Fieller coverage around 0.94",
        min(values) >= 0.93 and max(values) <= 0.95,
        "approximately\n$0.94$",
    )

    failed = [item for item in checks if not item[1]]
    for label, ok, detail in checks:
        print(f"[{'OK' if ok else 'FAIL'}] {label} ({detail})")
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed.")
    if failed:
        print("DRIFT: paper/main.tex disagrees with derived data.")
        sys.exit(1)
    print("All load-bearing paper numbers match the derived data.")


if __name__ == "__main__":
    main()
