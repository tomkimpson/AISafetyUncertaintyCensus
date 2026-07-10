#!/usr/bin/env python
"""Seed (and re-seed) the per-cell claim-fidelity audit log.

Every row of the census (``data/raw/census_full.md``, parsed with the SAME
``parse_census`` the paper's tables use, so IDs line up with Table 4) becomes one
row here, carrying the claimed (threshold, n, score, uncertainty, direction) and a
``value_status`` for whether the cited value was confirmed against the primary
source. Confirmations recorded in the ``VERIFIED`` table below are re-applied on
every run, so the audit trail is reproducible.

value_status:
  confirmed       — the cited value appears in the primary source at the cited locator
  confirmed_note  — value is faithful to the cited source but carries a documented caveat
  mismatch        — the claimed value is NOT supported by the cited source (needs fixing)
  unverified      — not yet checked

Output: ``data/verification/cell_audit.csv``.

    python scripts/seed_cell_audit.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from make_tables import parse_census  # noqa: E402  (reuse the canonical parser)

OUT = ROOT / "data" / "verification" / "cell_audit.csv"
PROV = ROOT / "data" / "verification" / "source_provenance.csv"

_FRAMEWORK_LETTER = {"Anthropic-RSP": "A", "OpenAI-PF": "O", "GDM-FSF": "D", "3rd-party": "T"}
_HEADER = {"Anthropic-RSP": "Anthropic", "OpenAI-PF": "OpenAI", "GDM-FSF": "DeepMind",
           "3rd-party": "3rd-party"}

# Source ids. The first block reuses the slugs in source_provenance.csv so the
# source_resolves join works; the second block are readable ids for sources added
# to MANIFEST.md during the primary-generation verification pass.
S_OPUS4 = "claude-opus-4-sonnet-4-system-card-may-2025"
S_37 = "claude-3-7-sonnet-system-card-feb-2025"
S_45 = "claude-opus-4-5-system-card-nov-2025"
S_46 = "claude-opus-4-6-system-card-feb-2026"
S_47 = "claude-opus-4-7-system-card-apr-2026"
S_48 = "claude-opus-4-8-system-card-may-2026"
S_G55 = "openai-gpt-5-5-system-card-apr-2026"
S_G56 = "openai-gpt-5-6-preview-system-card-25-jun-2026"
S_GEM3FSF = "deepmind-gemini-3-pro-fsf-report-nov-2025"
S_GEM31 = "deepmind-gemini-3-1-pro-model-card-feb-2026"
# These must match the slugs verify_sources.py writes into source_provenance.csv
# (slug = lowercased document name, non-alphanumerics -> '-', truncated to 60 chars),
# so the cell_audit -> provenance join is machine-checkable. Regenerate both together.
S_GPT4O = "openai-gpt-4o-system-card-arxiv-2410-21276"
S_O1 = "openai-o1-system-card-dec-2024"
S_O3 = "openai-o3-o4-mini-system-card-apr-2025"
S_PHUONG = "phuong-et-al-2024-evaluating-frontier-models-for-dangerous-c"
S_GEM25 = "google-deepmind-gemini-2-5-report-arxiv-2507-06261"
S_ARC = "arc-evals-kinniment-et-al-2023-arxiv-2312-11671"
S_METRO1 = "metr-openai-o1-preview-evaluation"
S_METR37 = "metr-claude-3-7-sonnet-evaluation"
S_HCAST = "metr-hcast-arxiv-2503-17354"
S_AISI = "uk-aisi-advanced-ai-evaluations-may-update-2024"
S_APOLLO = "apollo-research-in-context-scheming-arxiv-2412-04984"
S_35 = "claude-3-5-sonnet-model-card-addendum-jun-2024"

# Each entry: fw (required) + any of {domain (startswith), models (exact match on a
# "/"-split model token), model_sub (substring), cite (substring of citation)}.
# First matching entry wins, so exceptions/notes precede the broad group rows.
V = [
    # ======================= EXCEPTIONS / FLAGGED (must be first) =============
    # Gemini 3 Pro: the unsupported discrete solve counts were CORRECTED in
    # census_full.md on 2026-07-10 (see note); the cells now match the source.
    dict(fw="GDM-FSF", domain="Misalignment situational awareness", models=["Gemini 3 Pro"],
         status="confirmed", source=S_GEM3FSF, locator="FSF report p.16",
         note="CORRECTED 2026-07-10: original census cell '3/11' was not supported (the FSF report gives continuous normalized scores over 11 evals at 50 attempts each, ~Gemini 2.5 with a few upticks, no pass count, exploratory/no acceptance criteria). Cell now reflects the source."),
    dict(fw="GDM-FSF", domain="Misalignment stealth", models=["Gemini 3 Pro"],
         status="confirmed", source=S_GEM3FSF, locator="FSF report p.17 Fig 5",
         note="CORRECTED 2026-07-10: original census cell '1/4' was not supported (Fig 5 gives normalized 0-100 scores over 4 evals at 50 attempts, ~Gemini 2.5 except Oversight Pattern lower, no pass count). Cell now reflects the source."),
    dict(fw="GDM-FSF", domain="ML R&D RE-Bench", models=["Gemini 3 Pro"],
         status="confirmed_note", source=S_GEM3FSF, locator="FSF report Fig 4, p.15",
         note="7 tasks / 24 runs / 95% CI and 'below alert threshold' all confirmed; but the specific aggregate 1.04 is printed in the Gemini 3.1 model card, not the FSF report — re-cite the 1.04 to the 3.1 card."),
    dict(fw="Anthropic-RSP", domain="Autonomy AI-R&D AECI", models=["Opus 4.8"],
         status="confirmed_note", source=S_48, locator="§2.3.4-2.3.5 p.42-44",
         note="n=11 and AECI 155.5 confirmed; the phrase 'no sustained AI-attributable 2×' is an interpretive gloss, not verbatim in the cited section (which says 'does not cross the automated AI-R&D capability threshold'). Recommend softening/re-citing."),
    dict(fw="Anthropic-RSP", domain="Autonomy SWE-bench", models=["Opus 4.6"],
         status="confirmed_note", source=S_46, locator="§8.3.2 p.187-188",
         note="Confirmed as a NON-integer mean: 'solving on average 21.24 out of 45 problems ... below the 50% threshold of 22.5'. Correctly excluded from the auditable evals.csv (no integer pass count)."),
    dict(fw="OpenAI-PF", domain="Cyber CTF", model_sub=["GPT-4o"],
         status="confirmed_note", source=S_GPT4O, locator="Cybersecurity section",
         note="Solve percentages 19/0/1% confirmed. The 'buckets NOT REPORTED' annotation refers to per-difficulty challenge counts (denominators), which the card does not break out of the 172 total; the solve rates themselves are reported."),
    dict(fw="GDM-FSF", domain="Cyber in-house CTF", models=["Gemini 1.0", "Nano/Pro/Ultra 1.0"],
         status="confirmed_note", source=S_PHUONG, locator="Table 7",
         note="Values 3/2/0 confirmed; census writes them Ultra/Pro/Nano descending while Table 7 lists Nano/Pro/Ultra — ordering convention only."),
    dict(fw="GDM-FSF", domain="Cyber InterCode-CTF", models=["Gemini 1.0", "Nano/Pro/Ultra 1.0"],
         status="confirmed_note", source=S_PHUONG, locator="Table 6",
         note="Values 24/22/6 confirmed; Ultra/Pro/Nano ordering vs source Nano/Pro/Ultra."),
    dict(fw="Anthropic-RSP", domain="CBRN bioweapons knowledge", models=["Claude 3.7"],
         status="confirmed_note", source=S_37, locator="§7.1.4 p.27",
         note="3.7 card states 17/33 (the cited value). NOTE the later Opus 4 card retro-states 3.7 at 18/33 — a cross-card discrepancy on a human-graded eval; verdict unaffected (both far below 27/33). Consider a footnote."),
    dict(fw="Anthropic-RSP", domain="Autonomy SWE-bench", models=["Claude 3.7"],
         status="confirmed_note", source=S_37, locator="§7.2.2 p.30",
         note="9.65/42 (~23%) confirmed; the 3.7 card used '20 attempts' vs the Opus4-card '10 runs' convention — score unaffected."),

    # ======================= ANTHROPIC (primary generation) ===================
    dict(fw="Anthropic-RSP", domain="CBRN bio uplift", models=["Opus 4"], status="confirmed",
         source=S_OPUS4, locator="§7.2.4.1 p.90",
         note="Opus 4 63%±13% vs control 25%±13%; uplift 2.53×; thr ≤2.8×/≥5×; '±13%' undefined (no SD/SE/CI)."),
    dict(fw="Anthropic-RSP", domain="CBRN bio uplift", models=["Sonnet 4"], status="confirmed",
         source=S_OPUS4, locator="§7.2.4.1 p.90", note="Sonnet 4 42%±11%; uplift 1.70×."),
    dict(fw="Anthropic-RSP", domain="CBRN bio uplift", models=["Claude 3.7"], status="confirmed",
         source=S_37, locator="§7.1.4 p.25", note="27%±9% → 57%±20%; within-group uplift ~2.1×."),
    dict(fw="Anthropic-RSP", domain="CBRN bioweapons knowledge", models=["Opus 4", "Sonnet 4", "Opus 4 / Sonnet 4"],
         status="confirmed", source=S_OPUS4, locator="§7.2.4.5 p.94", note="Opus 4 & Sonnet 4 = 17/33; thr 27/33."),
    dict(fw="Anthropic-RSP", domain="CBRN long-form virology", models=["Claude 3.7"], status="confirmed",
         source=S_37, locator="§7.1.4 p.26", note="69.7% over 13 subtasks; zones <50%/>80%."),
    dict(fw="Anthropic-RSP", domain="CBRN long-form virology", models=["Opus 4"], status="confirmed",
         source=S_OPUS4, locator="§7.2.4.3 pp.91-92", note="task1 0.83 end-to-end, task2 pass@5 0.720."),
    dict(fw="Anthropic-RSP", domain="CBRN long-form virology", models=["Sonnet 4"], status="confirmed",
         source=S_OPUS4, locator="§7.2.4.3 p.92", note="task1 0.55, task2 0.635."),
    dict(fw="Anthropic-RSP", domain="CBRN creative biology", models=["Opus 4", "Sonnet 4", "Opus 4 / Sonnet 4"],
         status="confirmed", source=S_OPUS4, locator="§7.2.4.8 p.98", note="Opus 4 0.45±0.08; Sonnet 4 0.37±0.08."),
    dict(fw="Anthropic-RSP", domain="CBRN DNA-synth", models=["Opus 4", "Sonnet 4", "Opus 4 / Sonnet 4"],
         status="confirmed", source=S_OPUS4, locator="§7.2.4.6 pp.95-96", note="No model both assembled and evaded end-to-end."),
    dict(fw="Anthropic-RSP", domain="CBRN short-horizon comp-bio", models=["Opus 4", "Sonnet 4", "Opus 4 / Sonnet 4"],
         status="confirmed", source=S_OPUS4, locator="§7.2.4.9 p.99", note="4/6 below rule-out bar."),
    dict(fw="Anthropic-RSP", domain="Autonomy SWE-bench", models=["Opus 4"], status="confirmed",
         source=S_OPUS4, locator="§7.3.1 p.104", note="16.6/42; thr >50% over 10 runs on 42."),
    dict(fw="Anthropic-RSP", domain="Autonomy SWE-bench", models=["Sonnet 4"], status="confirmed",
         source=S_OPUS4, locator="§7.3.1 p.104", note="15.4/42."),
    dict(fw="Anthropic-RSP", domain="Autonomy METR data-dedup", models=["Opus 4"], status="confirmed",
         source=S_OPUS4, locator="§7.3.2 p.104", note="median F1 76.2%, 15/46 above thr."),
    dict(fw="Anthropic-RSP", domain="Autonomy METR data-dedup", models=["Sonnet 4"], status="confirmed",
         source=S_OPUS4, locator="§7.3.2 p.104", note="median F1 74.9%, 8/29 above thr."),
    dict(fw="Anthropic-RSP", domain="Autonomy METR data-dedup", models=["Claude 3.7"], status="confirmed",
         source=S_37, locator="§7.2.2 p.30", note="median F1 70.2%, 4/30 above thr."),
    dict(fw="Anthropic-RSP", domain="Cyber Web", models=["Opus 4"], status="confirmed",
         source=S_OPUS4, locator="§7.4.2 p.116", note="12/15 (pass@30)."),
    dict(fw="Anthropic-RSP", domain="Cyber Crypto", models=["Opus 4"], status="confirmed",
         source=S_OPUS4, locator="§7.4.3 p.116", note="8/22."),
    dict(fw="Anthropic-RSP", domain="Cyber Pwn", models=["Opus 4"], status="confirmed",
         source=S_OPUS4, locator="§7.4.3 p.117", note="5/9."),
    dict(fw="Anthropic-RSP", domain="Cyber Rev", models=["Opus 4"], status="confirmed",
         source=S_OPUS4, locator="§7.4.4 p.117", note="4/8."),
    dict(fw="Anthropic-RSP", domain="Cyber Network", models=["Opus 4"], status="confirmed",
         source=S_OPUS4, locator="§7.4.5 p.118", note="2/4."),
    dict(fw="Anthropic-RSP", domain="Cyber Cybench", models=["Opus 4", "Opus 4 / Sonnet 4"], status="confirmed",
         source=S_OPUS4, locator="§7.4.7 p.119", note="22/39 (1 of 40 not run)."),
    dict(fw="Anthropic-RSP", domain="Autonomy internal AI R&D suite", models=["Claude 3.7"], status="confirmed",
         source=S_37, locator="§7.2.1-7.2.2 pp.31-32", note="Internal suite of 7 environments; scores far below the human baseline (1.0)."),
    dict(fw="Anthropic-RSP", domain="Cyber Web/Crypto/Pwn/Rev/Net", models=["Claude 3.7"], status="confirmed",
         source=S_37, locator="§7.3.2 pp.35-37", note="Web 7/8, Crypto 3/4, Pwn 5/13, Rev 0/4, Net 0/4."),
    dict(fw="Anthropic-RSP", domain="Cyber Cybench", models=["Claude 3.7"], status="confirmed",
         source=S_37, locator="§7.3.2 p.37", note="15/34."),
    # Anthropic post-2025
    dict(fw="Anthropic-RSP", domain="Autonomy SWE-bench hard", models=["Opus 4.5"], status="confirmed",
         source=S_45, locator="§7.3.1 p.134", note="21/45; thr >50% over 10 trials on 45."),
    dict(fw="Anthropic-RSP", domain="CBRN short-horizon comp-bio", models=["Opus 4.5"], status="confirmed",
         source=S_45, locator="§7.2.4.6 p.128", note="3/6 crossed rule-out."),
    dict(fw="Anthropic-RSP", domain="CBRN long-form virology", models=["Opus 4.5"], status="confirmed",
         source=S_45, locator="§7.2.4.1 p.122", note="max@5 0.845 / pass@5 0.912."),
    dict(fw="Anthropic-RSP", domain="Autonomy AI-R&D AECI", models=["Opus 4.7"], status="confirmed",
         source=S_47, locator="§2.3.7 p.42", note="+1.0 AECI above ~13.6/yr slope (n=8); 95% CI error bars."),
    dict(fw="Anthropic-RSP", domain="CBRN DNA-synth", models=["Opus 4.8"], status="confirmed",
         source=S_48, locator="§2.2.6 p.29", note="7/10 pathogens evaded; not used for RSP determination."),
    dict(fw="Anthropic-RSP", domain="Aggregate", models=["Claude 3.5"], status="confirmed",
         source=S_35, locator="§3.1/§3.3 p.6",
         note="'Claude 3.5 Sonnet did not exceed our safety thresholds ... we classify it at ASL-2'; did not trigger the 4× effective-compute full-eval threshold."),

    # ======================= OPENAI (primary generation) ======================
    dict(fw="OpenAI-PF", model_sub=["GPT-4o"], status="confirmed", source=S_GPT4O,
         locator="GPT-4o System Card", note="ARA 0%/100 confirmed."),
    dict(fw="OpenAI-PF", model_sub=["o1"], status="confirmed", source=S_O1,
         locator="o1 System Card §5.x", note="CTF 46/13/13%, bio 350q→59%, SWE-bench 500→40.9%, MLE-bench 37%, etc. all confirmed."),
    dict(fw="OpenAI-PF", model_sub=["o3", "o4-mini"], status="confirmed", source=S_O3,
         locator="o3 & o4-mini System Card §4.3", note="CTF 89/68/59%, Pattern Labs 16/7/0 & 14/9/0 confirmed (pass@12)."),
    # OpenAI post-2025
    dict(fw="OpenAI-PF", model_sub=["GPT-5.5"], status="confirmed", source=S_G55,
         locator="GPT-5.5 System Card §9.x (deploymentsafety.openai.com/gpt-5-5)",
         note="TroubleshootingBench 44.1%, biochem 32.32%, CVE-Bench 34/40, UK AISI 90.5%±12.9% & 66.7%±15.9%, end-to-end 1/10 — all confirmed against the real card."),
    dict(fw="OpenAI-PF", model_sub=["GPT-5.6"], status="confirmed", source=S_G56,
         locator="GPT-5.6 Preview System Card §9.1.1.x",
         note="virology 55.5%, ProtocolQA 43.5%, tacit 84.1%, TSB 48.0%, AAV 0.529 vs 0.600, hard-neg & DNA below — all confirmed."),

    # ======================= DEEPMIND (primary generation) ====================
    dict(fw="GDM-FSF", cite=["2403.13793"], status="confirmed", source=S_PHUONG,
         locator="Phuong et al. 2024", note="Hidden Agenda 14%, Web of Lies 505/510/510, Hack The Box 0/13, self-proliferation credible intervals, self-reasoning — confirmed."),
    dict(fw="GDM-FSF", cite=["Gemini 2.5"], status="confirmed", source=S_GEM25,
         locator="Gemini 2.5 report Table 10 / Fig 9", note="offense 74/11/1, key-skills 7/14/6, stealth 2/5, sit-aware 2/11, CBRN MCQ, RE-Bench 50-125% — confirmed."),
    # DeepMind post-2025 (Gemini 3 Pro / 3.1); flagged rows handled in exceptions above
    dict(fw="GDM-FSF", cite=["FSF Report"], status="confirmed", source=S_GEM3FSF,
         locator="Gemini 3 Pro FSF Report", note="key-skills 11/12 & 0/13, harmful-manipulation 610 (421/189) sig — confirmed."),
    dict(fw="GDM-FSF", cite=["3.1 card"], status="confirmed", source=S_GEM31,
         locator="Gemini 3.1 Pro Model Card p.8", note="harmful-manip odds ratio 3.6×, RE-Bench 1.27 — confirmed."),

    # ======================= THIRD-PARTY =======================================
    dict(fw="3rd-party", cite=["ARC Evals"], status="confirmed", source=S_ARC,
         locator="Kinniment et al. 2023 (arXiv:2312.11671)", note="12-task ARA suite; agents complete easiest only."),
    dict(fw="3rd-party", cite=["METR o1-preview"], status="confirmed", source=S_METRO1,
         locator="METR o1-preview report", note="77 tasks/30 families ~35min; RE-Bench 7 tasks 2/7; 95% bootstrap CI in figures."),
    dict(fw="3rd-party", cite=["METR Claude 3.7"], status="confirmed_note", source=S_METR37,
         locator="METR Claude 3.7 report", note="96 tasks/37 families (exec summary; appendix says 97/38 — source-internal), 50%-horizon ~55min; RE-Bench 5 tasks @32h ~median expert."),
    dict(fw="3rd-party", cite=["2503.17354"], status="confirmed", source=S_HCAST,
         locator="HCAST (arXiv:2503.17354)", note="189 tasks."),
    dict(fw="3rd-party", cite=["UK AISI"], status="confirmed", source=S_AISI,
         locator="UK AISI May 2024", note="CTF 105 (top > half Pico); 600+ chem/bio Qs some ≈ experts."),
    dict(fw="3rd-party", cite=["2412.04984"], status="confirmed", source=S_APOLLO,
         locator="Apollo (arXiv:2412.04984)", note="6 evals, 5/6 schemed; o1 >85% deception persistence."),
]


def _tokens(model):
    return [t.strip() for t in model.split("/")]


def _match(row):
    toks = _tokens(row["model"])
    for v in V:
        if row["framework"] != v["fw"]:
            continue
        if "domain" in v and not row["domain"].startswith(v["domain"]):
            continue
        if "models" in v and not any(m in toks or m == row["model"] for m in v["models"]):
            continue
        if "model_sub" in v and not any(s in row["model"] for s in v["model_sub"]):
            continue
        if "cite" in v and not any(c in row["citation"] for c in v["cite"]):
            continue
        return v
    return None


def load_resolves():
    if not PROV.exists():
        return {}
    return {r["source_id"]: r["resolves"] for r in csv.DictReader(PROV.open())}


def main():
    parsed = parse_census()
    resolves = load_resolves()
    counters = {}
    rows = []
    for r in parsed:
        letter = _FRAMEWORK_LETTER.get(r["framework"], "X")
        counters[letter] = counters.get(letter, 0) + 1
        row_id = f"{letter}{counters[letter]}"
        v = _match(r)
        status = v["status"] if v else "unverified"
        source_id = v["source"] if v else ""
        rows.append({
            "row_id": row_id, "generation": r["generation"],
            "framework": _HEADER.get(r["framework"], r["framework"]),
            "domain": r["domain"], "model": r["model"],
            "claimed_threshold": r["threshold"], "claimed_n": r["n"],
            "claimed_score": r["score"], "claimed_uncertainty": r["ci"],
            "claimed_direction": r["direction"], "citation": r["citation"],
            "source_id": source_id,
            "source_resolves": resolves.get(source_id, "") if source_id else "",
            "cited_locator": v["locator"] if v else "",
            "value_status": status,
            "note": v.get("note", "") if v else "",
            "coder": "agent+source" if v else "", "date": "2026-07-10" if v else "",
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["row_id", "generation", "framework", "domain", "model",
              "claimed_threshold", "claimed_n", "claimed_score",
              "claimed_uncertainty", "claimed_direction", "citation",
              "source_id", "source_resolves", "cited_locator", "value_status",
              "note", "coder", "date"]
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    by = {}
    for r in rows:
        by[r["value_status"]] = by.get(r["value_status"], 0) + 1
    print(f"Seeded {len(rows)} census rows -> {OUT}")
    print(f"  status counts: {by}")
    mism = [r["row_id"] for r in rows if r["value_status"] == "mismatch"]
    unver = [r["row_id"] for r in rows if r["value_status"] == "unverified"]
    if mism:
        print(f"  MISMATCH rows (need fixing): {', '.join(mism)}")
    if unver:
        print(f"  unverified rows: {', '.join(unver)}")


if __name__ == "__main__":
    main()
