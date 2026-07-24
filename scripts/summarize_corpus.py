#!/usr/bin/env python
"""Summarize reporting at record, source-document, and framework levels.

The census record is a source-reported row or prose result, not an independent
draw. This script makes the two most useful denominators explicit:

* records: reporting units in ``census_records.csv``; and
* contributing source documents: unique ``source_id`` values with at least one
  eligible record.

It writes a compact aggregate file for the paper and a source-by-source audit
file that makes document concentration inspectable.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "raw" / "census_records.csv"
DERIVED = ROOT / "data" / "derived"
SUMMARY = DERIVED / "corpus_reporting_levels.csv"
SOURCES = DERIVED / "source_reporting.csv"

FRAMEWORK_ORDER = ("Anthropic", "OpenAI", "DeepMind", "3rd-party")


def _record_summary(rows):
    classes = Counter(r["uncertainty_class"] for r in rows)
    return {
        "total": len(rows),
        "no_uncertainty": classes["none"],
        "any_uncertainty": classes["proper_interval"] + classes["bare_dispersion"],
        "proper_interval": classes["proper_interval"],
        "bare_dispersion": classes["bare_dispersion"],
    }


def _source_rows(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["source_id"]].append(row)

    out = []
    for source_id, source_records in grouped.items():
        frameworks = {r["framework"] for r in source_records}
        if len(frameworks) != 1:
            raise ValueError(f"{source_id} crosses frameworks: {sorted(frameworks)}")
        counts = _record_summary(source_records)
        out.append({
            "source_id": source_id,
            "framework": next(iter(frameworks)),
            "eligible_records": counts["total"],
            "no_uncertainty_records": counts["no_uncertainty"],
            "any_uncertainty_records": counts["any_uncertainty"],
            "proper_interval_records": counts["proper_interval"],
            "bare_dispersion_records": counts["bare_dispersion"],
            "source_has_any_uncertainty": int(counts["any_uncertainty"] > 0),
            "source_has_proper_interval": int(counts["proper_interval"] > 0),
        })
    return sorted(out, key=lambda r: (r["framework"], r["source_id"]))


def _source_summary(rows):
    return {
        "total": len(rows),
        "no_uncertainty": sum(not int(r["source_has_any_uncertainty"]) for r in rows),
        "any_uncertainty": sum(int(r["source_has_any_uncertainty"]) for r in rows),
        "proper_interval": sum(int(r["source_has_proper_interval"]) for r in rows),
        "bare_dispersion": sum(
            int(r["source_has_any_uncertainty"])
            and not int(r["source_has_proper_interval"])
            for r in rows
        ),
    }


def main():
    with INPUT.open() as f:
        screened = list(csv.DictReader(f))
    eligible = [r for r in screened if r["include_primary"].lower() == "true"]
    source_rows = _source_rows(eligible)

    summary_rows = []
    for level in ("record", "source_document"):
        for framework in ("Overall", *FRAMEWORK_ORDER):
            if level == "record":
                selected = (
                    eligible
                    if framework == "Overall"
                    else [r for r in eligible if r["framework"] == framework]
                )
                counts = _record_summary(selected)
            else:
                selected = (
                    source_rows
                    if framework == "Overall"
                    else [r for r in source_rows if r["framework"] == framework]
                )
                counts = _source_summary(selected)
            summary_rows.append({
                "level": level,
                "framework": framework,
                **counts,
            })

    DERIVED.mkdir(parents=True, exist_ok=True)
    with SUMMARY.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "level", "framework", "total", "no_uncertainty",
                "any_uncertainty", "proper_interval", "bare_dispersion",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    with SOURCES.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(source_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(source_rows)

    overall_records = _record_summary(eligible)
    overall_sources = _source_summary(source_rows)
    print(
        f"eligible records: {overall_records['total']} "
        f"({overall_records['no_uncertainty']} with no uncertainty)"
    )
    print(
        f"contributing source documents: {overall_sources['total']} "
        f"({overall_sources['no_uncertainty']} with no uncertainty anywhere)"
    )
    print(f"wrote {SUMMARY}")
    print(f"wrote {SOURCES}")


if __name__ == "__main__":
    main()
