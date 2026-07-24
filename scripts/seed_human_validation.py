#!/usr/bin/env python
"""Create blank, row-addressed templates for independent human validation.

This script never copies the existing coding into the human fields. Two coders
should work from the pinned sources while blinded to one another and, as far as
practical, to the headline aggregate counts. Existing nonblank work is preserved
unless ``--force`` is passed.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "data" / "verification"
CENSUS = ROOT / "data" / "raw" / "census_records.csv"
EVALS = ROOT / "data" / "raw" / "evals.csv"


def _write(path, fieldnames, rows, force):
    if path.exists() and not force:
        print(f"preserved existing {path}; pass --force to replace")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote blank template {path} ({len(rows)} rows)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--force",
        action="store_true",
        help="replace existing templates (destructive to completed human coding)",
    )
    args = ap.parse_args()

    with CENSUS.open() as f:
        census = list(csv.DictReader(f))
    with EVALS.open() as f:
        evals = list(csv.DictReader(f))

    census_fields = [
        "record_id", "source_id", "coder_id", "source_checked",
        "include_primary", "n_status", "uncertainty_class", "notes", "status",
    ]
    census_rows = [
        {
            "record_id": row["record_id"],
            "source_id": row["source_id"],
            "coder_id": coder,
            "source_checked": "",
            "include_primary": "",
            "n_status": "",
            "uncertainty_class": "",
            "notes": "",
            "status": "pending",
        }
        for coder in ("HUMAN_A", "HUMAN_B")
        for row in census
    ]
    _write(
        VERIFY / "human_validation.csv",
        census_fields,
        census_rows,
        args.force,
    )

    census_adjudication_fields = [
        "record_id", "include_primary", "n_status", "uncertainty_class",
        "adjudicator", "resolution_notes", "status",
    ]
    census_adjudication_rows = [
        {
            "record_id": row["record_id"],
            "include_primary": "",
            "n_status": "",
            "uncertainty_class": "",
            "adjudicator": "",
            "resolution_notes": "",
            "status": "pending",
        }
        for row in census
    ]
    _write(
        VERIFY / "human_adjudication.csv",
        census_adjudication_fields,
        census_adjudication_rows,
        args.force,
    )

    audit_fields = [
        "record_id", "capability", "model", "coder_id", "source_checked",
        "reported_score", "reconstructed_n", "reconstructed_successes",
        "operative_threshold", "mapping_notes", "status",
    ]
    audit_rows = [
        {
            "record_id": row["record_id"],
            "capability": row["capability"],
            "model": row["model"],
            "coder_id": coder,
            "source_checked": "",
            "reported_score": "",
            "reconstructed_n": "",
            "reconstructed_successes": "",
            "operative_threshold": "",
            "mapping_notes": "",
            "status": "pending",
        }
        for coder in ("HUMAN_A", "HUMAN_B")
        for row in evals
    ]
    _write(
        VERIFY / "model_audit_validation.csv",
        audit_fields,
        audit_rows,
        args.force,
    )

    audit_adjudication_fields = [
        "record_id", "capability", "model", "reported_score",
        "reconstructed_n", "reconstructed_successes", "operative_threshold",
        "adjudicator", "resolution_notes", "status",
    ]
    audit_adjudication_rows = [
        {
            "record_id": row["record_id"],
            "capability": row["capability"],
            "model": row["model"],
            "reported_score": "",
            "reconstructed_n": "",
            "reconstructed_successes": "",
            "operative_threshold": "",
            "adjudicator": "",
            "resolution_notes": "",
            "status": "pending",
        }
        for row in evals
    ]
    _write(
        VERIFY / "model_audit_adjudication.csv",
        audit_adjudication_fields,
        audit_adjudication_rows,
        args.force,
    )


if __name__ == "__main__":
    main()
