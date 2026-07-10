# Source manifest — vendor-attested documents

Reproducibility record for every vendor/system-card source the paper relies on, especially
those published after the assistant knowledge cutoff. For each: the canonical URL, the date
retrieved, and (where the PDF was downloaded during analysis) a SHA-256 of the file. To
re-verify, download the URL and recompute `shasum -a 256`. Where a live capture was not
downloaded, request a Wayback Machine snapshot at `https://web.archive.org/web/*/<url>` and
record the dated snapshot URL alongside.

Large binaries and vendor-copyrighted content are intentionally NOT committed to the repo;
this manifest plus the URLs and hashes is the archival record. The key passage for the case
study is Opus 4 System Card §7.2.4.1 (see the hashed URL below).

## Audited generation

| document | url | retrieved | sha-256 |
|---|---|---|---|
| Claude Opus 4 & Sonnet 4 System Card (May 2025) | https://www-cdn.anthropic.com/4263b940cabb546aa0e3283f35b686f4f3b2ff47.pdf | 2026-07-03 | `48d4d98c5767d02308ba68b595e344c4fd53fbef11f0f9ac351e8752a9129764` |
| Claude 3.7 Sonnet System Card (Feb 2025) | https://www.anthropic.com/claude-3-7-sonnet-system-card | pending | — |

## Post-2025 generation (post knowledge cutoff — archive before submission)

| document | url | retrieved | sha-256 |
|---|---|---|---|
| Claude Opus 4.5 System Card (Nov 2025) | https://assets.anthropic.com/m/64823ba7485345a7/Claude-Opus-4-5-System-Card.pdf | pending | — |
| Claude Opus 4.6 System Card (Feb 2026) | https://www-cdn.anthropic.com/6a5fa276ac68b9aeb0c8b6af5fa36326e0e166dd.pdf | pending | — |
| Claude Opus 4.7 System Card (Apr 2026) | (locate on anthropic.com/system-cards) | pending | — |
| Claude Opus 4.8 System Card (May 2026) | https://www-cdn.anthropic.com/0b4915911bb0d19eca5b5ee635c80fef830a37ea.pdf | pending | — |
| Anthropic RSP v3.3 (May 2026) | https://www.anthropic.com/rsp | pending | — |
| OpenAI GPT-5.5 System Card (Apr 2026) | https://openai.com/index/gpt-5-5-system-card/ | pending | — |
| OpenAI GPT-5.6 Preview System Card (25 Jun 2026) | https://deploymentsafety.openai.com/gpt-5-6-preview/ | pending | — |
| DeepMind Gemini 3 Pro FSF Report (Nov 2025) | (locate on deepmind.google) | pending | — |
| RAND cyber-uplift RCT (2026) | (locate on rand.org) | pending | — |

## Downstream-use receipts (§3)

| document | url | retrieved |
|---|---|---|
| Epoch AI — biorisk evaluations (Ho & Berg, Jun 2025) | https://epoch.ai/gradient-updates/do-the-biorisk-evaluations-of-ai-labs-actually-measure-the-risk-of-developing-bioweapons | 2026-07-03 |
| TIME — Claude 4 safeguards (Perrigo, May 2025) | https://time.com/7287806/anthropic-claude-4-opus-safety-bio-risk/ | 2026-07-03 (title via search; page 403 to bot) |
| CNBC — Claude 4 security measures (May 2025) | https://www.cnbc.com/2025/05/23/anthropic-claude-4-weapons.html | 2026-07-03 |

**Note.** URLs marked `pending` are cited in the manuscript from the census/prior sessions
but were not re-downloaded and hashed in this session; hash them (or record a Wayback
snapshot) before arXiv submission. The Opus 4 card is the one document the headline case
depends on and is fully hashed.
