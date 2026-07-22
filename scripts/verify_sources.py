#!/usr/bin/env python
"""Resolve, hash, and archive every source cited in the census provenance manifest.

Reads the markdown tables in ``data/raw/sources/MANIFEST.md``, extracts each
(document, URL) pair, and for every resolvable URL records:

* the final URL after redirects and the HTTP status,
* the content-type and byte length,
* a SHA-256 of the downloaded bytes (the archival fingerprint), and
* a Wayback Machine snapshot URL (via the availability API) as the third-party
  fallback when the live URL later rots.

Output: ``data/verification/source_provenance.csv``. This is the deterministic,
re-runnable half of the census verification: a third party runs it and compares
the SHA-256 column against ``MANIFEST.md``. Claim-fidelity (does the document
actually say what the census claims?) is tracked separately in
``data/verification/cell_audit.csv``.

Downloaded files are cached under ``data/verification/cache/`` (gitignored) so the
cited pages can be re-read without re-fetching; vendor PDFs are never committed.

Usage:
    python scripts/verify_sources.py [--no-download] [--timeout 30]
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "raw" / "sources" / "MANIFEST.md"
OUT = ROOT / "data" / "verification" / "source_provenance.csv"
CACHE = ROOT / "data" / "verification" / "cache"

# A browser-like UA: several vendor hosts (openai.com, news sites) 403 a bare
# urllib agent. This is a plain GET of a public page, no auth.
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
MAX_BYTES = 80 * 1024 * 1024  # guard against a pathological download
_URL_RE = re.compile(r"https?://[^\s)>\]]+")


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s[:60] or "source"


def parse_manifest(text: str):
    """Yield dicts {document, url, retrieved, sha_manifest} from every markdown
    table row that has a document name in the first cell. URL may be None when the
    manifest carries a placeholder like ``(locate on deepmind.google)``."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        head = cells[0].lower()
        if head in ("document", "") or set(cells[0]) <= {"-", ":", " "}:
            continue  # header or separator row
        doc = cells[0]
        m = _URL_RE.search(cells[1])
        url = m.group(0) if m else None
        retrieved = cells[2] if len(cells) > 2 else ""
        sha_manifest = ""
        if len(cells) > 3:
            sm = re.search(r"[0-9a-f]{64}", cells[3])
            sha_manifest = sm.group(0) if sm else ""
        rows.append({"document": doc, "url": url,
                     "retrieved": retrieved, "sha_manifest": sha_manifest})
    return rows


def wayback(url: str, timeout: int) -> str:
    api = "https://archive.org/wayback/available?url=" + urllib.request.quote(url, safe="")
    try:
        req = urllib.request.Request(api, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        snap = data.get("archived_snapshots", {}).get("closest", {})
        return snap.get("url", "") if snap.get("available") else ""
    except Exception:
        return ""


def fetch(url: str, download: bool, timeout: int, cache_name: str):
    """Return (resolves, status, final_url, content_type, nbytes, sha256, note)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status = getattr(r, "status", r.getcode())
            final_url = r.geturl()
            ctype = r.headers.get("content-type", "")
            if not download:
                return "Y", status, final_url, ctype, "", "", "resolved (not downloaded)"
            h = hashlib.sha256()
            n = 0
            CACHE.mkdir(parents=True, exist_ok=True)
            ext = ".pdf" if "pdf" in ctype.lower() or url.lower().endswith(".pdf") else ".html"
            dest = CACHE / (cache_name + ext)
            with dest.open("wb") as f:
                while True:
                    chunk = r.read(1 << 16)
                    if not chunk:
                        break
                    n += len(chunk)
                    if n > MAX_BYTES:
                        return ("Y", status, final_url, ctype, str(n), "",
                                "exceeded MAX_BYTES; hash aborted")
                    h.update(chunk)
                    f.write(chunk)
            return "Y", status, final_url, ctype, str(n), h.hexdigest(), f"cached {dest.name}"
    except urllib.error.HTTPError as e:
        return "N", e.code, url, "", "", "", f"HTTPError {e.code}"
    except Exception as e:  # noqa: BLE001
        return "N", "", url, "", "", "", f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-download", action="store_true",
                    help="resolve only; skip download/hash (faster, no cache)")
    ap.add_argument("--timeout", type=int, default=30)
    args = ap.parse_args()

    entries = parse_manifest(MANIFEST.read_text())
    today = _dt.date.today().isoformat()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    fields = ["source_id", "document", "url", "resolves", "http_status",
              "final_url", "content_type", "bytes", "sha256", "sha_manifest",
              "sha_matches_manifest", "wayback_url", "retrieved", "checked", "notes"]
    out_rows = []
    seen = {}
    for e in entries:
        sid = slug(e["document"])
        seen[sid] = seen.get(sid, 0) + 1
        if seen[sid] > 1:
            sid = f"{sid}-{seen[sid]}"
        if not e["url"]:
            out_rows.append({**{k: "" for k in fields}, "source_id": sid,
                             "document": e["document"], "url": "",
                             "resolves": "N", "retrieved": e["retrieved"],
                             "checked": today,
                             "notes": "no URL in manifest (placeholder)"})
            print(f"[--] {sid}: no URL (placeholder)")
            continue
        resolves, status, final_url, ctype, nbytes, sha, note = fetch(
            e["url"], download=not args.no_download, timeout=args.timeout,
            cache_name=sid)
        wb = wayback(e["url"], args.timeout)
        match = ""
        if sha and e["sha_manifest"]:
            match = "Y" if sha == e["sha_manifest"] else "N"
        out_rows.append({
            "source_id": sid, "document": e["document"], "url": e["url"],
            "resolves": resolves, "http_status": status, "final_url": final_url,
            "content_type": ctype, "bytes": nbytes, "sha256": sha,
            "sha_manifest": e["sha_manifest"], "sha_matches_manifest": match,
            "wayback_url": wb, "retrieved": e["retrieved"], "checked": today,
            "notes": note,
        })
        flag = "OK" if resolves == "Y" else "!!"
        print(f"[{flag}] {sid}: {resolves} status={status} "
              f"{'sha=' + sha[:12] if sha else ''} "
              f"{'wayback' if wb else 'no-wayback'} {note}")

    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)

    n_ok = sum(1 for r in out_rows if r["resolves"] == "Y")
    n_bad = [r["source_id"] for r in out_rows if r["resolves"] != "Y"]
    print(f"\n{n_ok}/{len(out_rows)} sources resolved -> {OUT}")
    if n_bad:
        print(f"UNRESOLVED ({len(n_bad)}): {', '.join(n_bad)}")


if __name__ == "__main__":
    main()
