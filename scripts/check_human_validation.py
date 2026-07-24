#!/usr/bin/env python
"""Submission gate for independent human validation and adjudication.

The gate intentionally fails while any row is pending. Once complete, it checks
the two independent coder files, validates allowed values, prints raw agreement
and Cohen's kappa for categorical corpus fields, and confirms that every row has
an adjudicated value. It does not silently overwrite the canonical corpus.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "data" / "verification"

CENSUS_ALLOWED = {
    "include_primary": {"true", "false"},
    "n_status": {"score_denominator", "partial_or_indirect", "not_reported"},
    "uncertainty_class": {"proper_interval", "bare_dispersion", "none"},
}


def _read(name):
    path = VERIFY / name
    if not path.exists():
        sys.exit(f"MISSING: {path}; run scripts/seed_human_validation.py")
    with path.open() as f:
        return list(csv.DictReader(f))


def _require_complete(name, rows):
    pending = [r for r in rows if r.get("status", "").strip().lower() != "complete"]
    if pending:
        print(f"PENDING: {name}: {len(pending)}/{len(rows)} rows are not complete")
        return False
    return True


def _validate_allowed(name, rows, allowed):
    ok = True
    for field, values in allowed.items():
        bad = [r for r in rows if r.get(field, "").strip().lower() not in values]
        if bad:
            print(f"INVALID: {name}: {len(bad)} rows have an invalid {field}")
            ok = False
    return ok


def _kappa(left, right):
    if len(left) != len(right) or not left:
        raise ValueError("paired, nonempty coder vectors required")
    observed = sum(a == b for a, b in zip(left, right)) / len(left)
    left_p = Counter(left)
    right_p = Counter(right)
    categories = set(left_p) | set(right_p)
    expected = sum(
        (left_p[c] / len(left)) * (right_p[c] / len(right))
        for c in categories
    )
    kappa = (observed - expected) / (1 - expected) if expected < 1 else 1.0
    return observed, kappa


def _paired_census(rows):
    by_id = defaultdict(dict)
    for row in rows:
        by_id[row["record_id"]][row["coder_id"]] = row
    bad = [record_id for record_id, pair in by_id.items() if set(pair) != {"HUMAN_A", "HUMAN_B"}]
    if bad:
        raise ValueError(f"{len(bad)} census records lack exactly HUMAN_A and HUMAN_B")
    return [
        (record_id, pair["HUMAN_A"], pair["HUMAN_B"])
        for record_id, pair in sorted(by_id.items())
    ]


def _audit_key(row):
    return row["record_id"], row["capability"], row["model"]


def _paired_audit(rows):
    by_key = defaultdict(dict)
    for row in rows:
        by_key[_audit_key(row)][row["coder_id"]] = row
    bad = [key for key, pair in by_key.items() if set(pair) != {"HUMAN_A", "HUMAN_B"}]
    if bad:
        raise ValueError(f"{len(bad)} audit results lack exactly HUMAN_A and HUMAN_B")
    return [
        (key, pair["HUMAN_A"], pair["HUMAN_B"])
        for key, pair in sorted(by_key.items())
    ]


def main():
    census = _read("human_validation.csv")
    census_final = _read("human_adjudication.csv")
    audit = _read("model_audit_validation.csv")
    audit_final = _read("model_audit_adjudication.csv")

    complete = all([
        _require_complete("human_validation.csv", census),
        _require_complete("human_adjudication.csv", census_final),
        _require_complete("model_audit_validation.csv", audit),
        _require_complete("model_audit_adjudication.csv", audit_final),
    ])
    if not complete:
        print("Human-validation submission gate remains closed.")
        sys.exit(1)

    ok = _validate_allowed("human_validation.csv", census, CENSUS_ALLOWED)
    ok &= _validate_allowed("human_adjudication.csv", census_final, CENSUS_ALLOWED)
    if any(r.get("source_checked", "").strip().lower() != "yes" for r in census):
        print("INVALID: every independent census row must have source_checked=yes")
        ok = False
    if any(r.get("source_checked", "").strip().lower() != "yes" for r in audit):
        print("INVALID: every independent audit row must have source_checked=yes")
        ok = False

    try:
        census_pairs = _paired_census(census)
        audit_pairs = _paired_audit(audit)
    except ValueError as exc:
        print(f"INVALID: {exc}")
        sys.exit(1)

    final_census_ids = {r["record_id"] for r in census_final}
    paired_census_ids = {record_id for record_id, _, _ in census_pairs}
    if final_census_ids != paired_census_ids:
        print("INVALID: census adjudication IDs do not match independent coding IDs")
        ok = False

    final_audit_keys = {_audit_key(r) for r in audit_final}
    paired_audit_keys = {key for key, _, _ in audit_pairs}
    if final_audit_keys != paired_audit_keys:
        print("INVALID: audit adjudication keys do not match independent coding keys")
        ok = False

    print("Independent corpus-coding reliability:")
    for field in CENSUS_ALLOWED:
        left = [a[field].strip().lower() for _, a, _ in census_pairs]
        right = [b[field].strip().lower() for _, _, b in census_pairs]
        agreement, kappa = _kappa(left, right)
        print(f"  {field}: agreement={agreement:.3f}; Cohen kappa={kappa:.3f}")

    audit_fields = (
        "reported_score", "reconstructed_n", "reconstructed_successes",
        "operative_threshold",
    )
    print("Independent model-audit exact agreement:")
    for field in audit_fields:
        agreement = sum(a[field] == b[field] for _, a, b in audit_pairs) / len(audit_pairs)
        print(f"  {field}: {agreement:.3f}")

    if not ok:
        sys.exit(1)
    print("PASS: human validation and adjudication are complete.")


if __name__ == "__main__":
    main()
