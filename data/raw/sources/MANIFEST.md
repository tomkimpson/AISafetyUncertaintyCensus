# Source manifest — vendor-attested documents

Reproducibility record for every vendor/system-card source the paper relies on, especially
those published after the assistant knowledge cutoff. For each: the canonical URL, the date
retrieved, and a fingerprint for re-verification.

**How to re-verify.** Run `python scripts/verify_sources.py`. It reads this file, resolves
every URL, downloads it, records a SHA-256, and looks up a Wayback snapshot, writing
`data/verification/source_provenance.csv`. Then:

- **PDFs** have a *stable* SHA-256 — re-download and `shasum -a 256` must match the value
  below. This is the archival fingerprint.
- **HTML pages** (RSP, GPT-5.5/5.6 cards, RAND, news) return *different* bytes on each fetch
  (dynamic markup, embedded timestamps), so their SHA-256 is **not** reproducible and is
  intentionally not pinned here. For HTML, the archival anchor is the **Wayback snapshot**
  URL: cite the dated snapshot, not the live page. The stable content for the OpenAI cards
  also exists in their downloadable PDF form where offered.

Large binaries and vendor-copyrighted content are intentionally NOT committed to the repo;
this manifest plus the URLs, hashes, and Wayback snapshots is the archival record. Cached
copies land in `data/verification/cache/` (gitignored) for local page-level re-reading.
All URLs below were resolved and fingerprinted on **2026-07-10** (retrieval dates in the
tables are the census-construction retrieval; `checked` in the provenance CSV is the
re-verification date).

## Audited generation (the nine machine-auditable rows depend on these)

| document | url | retrieved | sha-256 (PDF) |
|---|---|---|---|
| Claude Opus 4 & Sonnet 4 System Card (May 2025) | https://www-cdn.anthropic.com/4263b940cabb546aa0e3283f35b686f4f3b2ff47.pdf | 2026-07-03 | `48d4d98c5767d02308ba68b595e344c4fd53fbef11f0f9ac351e8752a9129764` |
| Claude 3.7 Sonnet System Card (Feb 2025) | https://www.anthropic.com/claude-3-7-sonnet-system-card | 2026-07-10 | `82947a46fc2d1b9a1d69501ef973fc3c5b328b703b9a17bd8a143c2672f8a1a6` (resolves to `www-cdn.anthropic.com/.../claude-3-7-sonnet-system-card.pdf`) |
| Claude 3.5 Sonnet Model Card Addendum (Jun 2024) | https://www-cdn.anthropic.com/fed9cc193a14b84131812372d8d5857f8f304c52/Model_Card_Claude_3_Addendum.pdf | 2026-07-10 | (PDF; hashed by verify_sources) — §3.3 states ASL-2, did not exceed thresholds |
| Claude Opus 4.5 System Card (Nov 2025) | https://assets.anthropic.com/m/64823ba7485345a7/Claude-Opus-4-5-System-Card.pdf | 2026-07-10 | `33be92efcb58f901d9d2c17e61bf277afbd514a1ac70a642f21e918c21ca25a8` (301 → `www-cdn.anthropic.com/bf10f64990cfda0ba858290be7b8cc6317685f47.pdf`) |

## Post-2025 generation (published after the census-building assistant's knowledge cutoff)

All resolved, hashed, and Wayback-archived on 2026-07-10 (2026-07-10 turned the previously
`pending` entries live).

| document | url | retrieved | sha-256 (PDF) / archival anchor |
|---|---|---|---|
| Claude Opus 4.6 System Card (Feb 2026) | https://www-cdn.anthropic.com/6a5fa276ac68b9aeb0c8b6af5fa36326e0e166dd.pdf | 2026-07-10 | `4db67c6b6aea0a87e7f8a784b83fc05a0f1a61a3e87615fe7956e3486b951b3c` |
| Claude Opus 4.7 System Card (Apr 2026) | https://www-cdn.anthropic.com/037f06850df7fbe871e206dad004c3db5fd50340/Claude%20Opus%204.7%20System%20Card.pdf | 2026-07-10 | `a7729a0e5eb61dc6818f553ae3c27ab774411cd5ab4ed7f414456d74a05c26d2` |
| Claude Opus 4.8 System Card (May 2026) | https://www-cdn.anthropic.com/0b4915911bb0d19eca5b5ee635c80fef830a37ea.pdf | 2026-07-10 | `97f11ae3fb305c7105c958599bcf90f216669543393220f674610ddb83ee611a` |
| Anthropic RSP v3.3 (May 2026) | https://www.anthropic.com/rsp | 2026-07-10 | HTML (301 → `/responsible-scaling-policy`; page shows current v3.4 + v3.3 history); use Wayback |
| OpenAI GPT-5.5 System Card (Apr 2026) | https://deploymentsafety.openai.com/gpt-5-5/ | 2026-07-10 | HTML (multi-page; §9.x). NOTE: `openai.com/index/gpt-5-5-system-card/` is only a marketing landing page with none of the benchmark content — the actual card lives on the Deployment Safety Hub at this URL. Use Wayback. |
| OpenAI GPT-5.6 Preview System Card (25 Jun 2026) | https://deploymentsafety.openai.com/gpt-5-6-preview/ | 2026-07-10 | HTML; Wayback `web.archive.org/web/20260708195649/https://deploymentsafety.openai.com/gpt-5-6-preview` |
| DeepMind Gemini 3 Pro FSF Report (Nov 2025) | https://storage.googleapis.com/deepmind-media/gemini/gemini_3_pro_fsf_report.pdf | 2026-07-10 | `0b093ee5fc80e30fa5b46e6aa9a853c6dd3f308656e9c9a346724e108e620e46` |
| DeepMind Gemini 3 Pro Model Card (Nov 2025) | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-Pro-Model-Card.pdf | 2026-07-10 | `9a1734bc3aa310691772d1756990b01383dc7732d4f9cb0a2888e2e06a7f84d8` |
| DeepMind Gemini 3.1 Pro Model Card (Feb 2026) | https://deepmind.google/models/model-cards/gemini-3-1-pro/ | 2026-07-10 | HTML; use Wayback |
| RAND cyber-uplift RCT — human uplift study (2026) | https://www.rand.org/pubs/research_reports/RRA3892-1.html | 2026-07-10 | HTML; Wayback `web.archive.org/web/20260626032730/https://www.rand.org/pubs/research_reports/RRA3892-1.html` |

## Primary generation — non-Anthropic vendor sources (located & verified 2026-07-10)

These back the OpenAI and DeepMind rows of the census. Added after the per-cell
verification pass located them (they were previously implicit in `census_full.md`
citations only).

| document | url | retrieved | sha-256 (PDF) / anchor |
|---|---|---|---|
| OpenAI GPT-4o System Card (arXiv:2410.21276) | https://arxiv.org/pdf/2410.21276 | 2026-07-10 | (PDF; hashed by verify_sources) |
| OpenAI o1 System Card (Dec 2024) | https://cdn.openai.com/o1-system-card-20241205.pdf | 2026-07-10 | (PDF; hashed by verify_sources) |
| OpenAI o3 & o4-mini System Card (Apr 2025) | https://cdn.openai.com/pdf/2221c875-02dc-4789-800b-e7758f3722c1/o3-and-o4-mini-system-card.pdf | 2026-07-10 | (PDF; hashed by verify_sources) |
| Phuong et al. 2024, Evaluating Frontier Models for Dangerous Capabilities (arXiv:2403.13793) | https://arxiv.org/pdf/2403.13793 | 2026-07-10 | `89225ba18d3823a3b766d00833bf77c4540749b4279a2628c1f78e15aadb560e` |
| Google DeepMind Gemini 2.5 report (arXiv:2507.06261) | https://storage.googleapis.com/deepmind-media/gemini/gemini_v2_5_report.pdf | 2026-07-10 | `d10cf3e99841b6411901de4a1fb8538a3cd9aab3cc84880941811d8dd7e86a1a` |

## Third-party evaluators (located & verified 2026-07-10)

Back the METR / UK AISI / Apollo / ARC / HCAST rows of the census.

| document | url | retrieved | anchor |
|---|---|---|---|
| ARC Evals — Kinniment et al. 2023 (arXiv:2312.11671) | https://arxiv.org/pdf/2312.11671 | 2026-07-10 | (PDF) |
| METR — OpenAI o1-preview evaluation | https://metr.org/evaluations/openai-o1-preview-report/ | 2026-07-10 | HTML; use Wayback |
| METR — Claude 3.7 Sonnet evaluation | https://metr.org/evaluations/claude-3-7-report/ | 2026-07-10 | HTML; use Wayback |
| METR — HCAST (arXiv:2503.17354) | https://arxiv.org/pdf/2503.17354 | 2026-07-10 | (PDF) |
| UK AISI — Advanced AI evaluations, May update (2024) | https://www.aisi.gov.uk/blog/advanced-ai-evaluations-may-update | 2026-07-10 | HTML; use Wayback |
| Apollo Research — in-context scheming (arXiv:2412.04984) | https://arxiv.org/pdf/2412.04984 | 2026-07-10 | (PDF) |

## Downstream-use receipt

| document | url | retrieved | archival anchor |
|---|---|---|---|
| Epoch AI — biorisk evaluations (Ho & Berg, Jun 2025) | https://epoch.ai/gradient-updates/do-the-biorisk-evaluations-of-ai-labs-actually-measure-the-risk-of-developing-bioweapons | 2026-07-03 | HTML; Wayback available |

(The TIME and CNBC press pieces were previously listed here but are not cited in
the manuscript, so they have been dropped from `references.bib` and this manifest.)

## Status (2026-07-10)

- **16 / 16 sources resolve.** Every source the census cites now has a live URL; the three
  former placeholders (Opus 4.7, Gemini 3 FSF report, RAND RCT) were located and added, and
  the Gemini 3 Pro / 3.1 Pro model cards were disambiguated.
- **All PDF sources carry a stable SHA-256** recorded above and machine-checkable via
  `scripts/verify_sources.py`. The Opus 4 card — the one document the headline case study
  depends on — hashes byte-identical to the value first recorded on 2026-07-03.
- **HTML sources are anchored to Wayback snapshots** rather than SHA (their bytes vary per
  fetch). Full snapshot URLs are in `data/verification/source_provenance.csv`.
- Claim-fidelity (does each cited document actually state the census's numbers?) is tracked
  per row in `data/verification/cell_audit.csv`, not here.
