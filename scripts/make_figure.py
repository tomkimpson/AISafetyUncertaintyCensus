#!/usr/bin/env python
"""The headline figure: confidence intervals against decision thresholds.

A grouped forest plot. Each audited row is drawn as its reported score (point)
with its one-sided 95% directional bounds (thick bar) against the group's decision threshold (vertical
line); a thin grey whisker behind shows the CI widened to the effective sample
size under item clustering (ICC=0.2 at the assumed cluster size), where
clustering applies. Rows whose naive CI crosses the threshold cannot resolve
it and are drawn in vermilion with an open marker (redundant encoding for
grayscale). Reads data/derived/audited.csv (produced by run_audit.py) and
writes paper/figures/ci_straddle.{pdf,png}.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# Okabe-Ito: distinguishable under all common forms of colour blindness.
BLUE = "#0072B2"       # resolved
VERMILION = "#D55E00"  # cannot resolve
INK = "#1a1a1a"        # threshold line, headers
GREY = "#999999"       # clustered whisker, secondary text
LIGHTGREY = "#c8c8c8"

GROUPS = [
    ("swebench_hard", "SWE-bench (hard subset)", r"$\tau = 0.50$"),
    ("metr_dedup", "METR data deduplication", r"$\tau = 0.20$"),
    ("bioweapons_knowledge", "Bioweapons acquisition knowledge", r"$\tau = 0.82$ (27/33)"),
]
MODEL_ORDER = ["Opus 4.5", "Opus 4", "Sonnet 4", "Claude 3.7"]

ROW_H = 1.0      # vertical distance between data rows
HEAD_H = 1.0     # header to first row
GAP_H = 0.55     # extra gap between groups


def fmt_prob(p: float) -> str:
    if p < 0.001:
        return "< 0.001"
    if p > 0.999:
        return "> 0.999"
    return f"{p:.2f}"


def main():
    infile = ROOT / "data/derived/audited.csv"
    if not infile.exists():
        sys.exit("run scripts/run_audit.py first")
    rows = list(csv.DictReader(open(infile)))
    by_group = {key: sorted((r for r in rows if r["capability"] == key),
                            key=lambda r: MODEL_ORDER.index(r["model"]))
                for key, _, _ in GROUPS}

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 8,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.8,
        "pdf.fonttype": 42,  # embed TrueType so text stays editable/searchable
        "ps.fonttype": 42,
    })

    n_rows = sum(len(v) for v in by_group.values())
    fig_h = 0.38 * (n_rows + len(GROUPS) * (HEAD_H + GAP_H) / ROW_H) + 0.9
    fig, ax = plt.subplots(figsize=(7.2, fig_h))

    # Lay out rows top-to-bottom, remembering y-extent of each group for the
    # threshold segment.
    y = 0.0
    ticks_y, ticks_label = [], []
    for key, gname, gthr in GROUPS:
        grows = by_group[key]
        thr = float(grows[0]["threshold"])
        y_head = y
        y -= HEAD_H
        y_first = y
        for r in grows:
            score = float(r["score"])
            lo, hi = float(r["directional_low"]), float(r["directional_high"])
            straddle = bool(int(r["unresolved_primary"]))
            color = VERMILION if straddle else BLUE

            # Clustered CI (where clustering applies) as a thin grey whisker
            # behind the naive bar.
            lo_c, hi_c = r.get("directional_low_clust"), r.get("directional_high_clust")
            if lo_c and hi_c and r.get("assumed_m"):
                for x in (float(lo_c), float(hi_c)):
                    ax.plot([x, x], [y - 0.14, y + 0.14], color=GREY,
                            lw=0.9, zorder=2)
                ax.plot([float(lo_c), float(hi_c)], [y, y], color=GREY,
                        lw=0.9, zorder=2)

            ax.plot([lo, hi], [y, y], color=color, lw=2.2,
                    solid_capstyle="butt", zorder=3)
            for x in (lo, hi):
                ax.plot([x, x], [y - 0.18, y + 0.18], color=color, lw=1.6,
                        zorder=3)
            ax.plot(score, y, marker="o", ms=6, zorder=4,
                    markerfacecolor="white" if straddle else color,
                    markeredgecolor=color, markeredgewidth=1.4)

            ticks_y.append(y)
            ticks_label.append(r["model"])
            # Secondary columns: n (left of axis) and posterior (right).
            ax.text(-0.015, y, f"$n$ = {r['n']}", transform=ax.get_yaxis_transform(),
                    ha="right", va="center", fontsize=7, color=GREY)
            ax.text(1.02, y, fmt_prob(float(r["prob_above"])),
                    transform=ax.get_yaxis_transform(),
                    ha="left", va="center", fontsize=7.5, color=INK)
            y -= ROW_H
        y_last = y + ROW_H

        # Threshold segment spans the group up to just below its header label.
        ax.plot([thr, thr], [y_last - 0.42, y_head - 0.30], color=INK,
                lw=1.4, zorder=5)
        ax.text(-0.28, y_head, gname, transform=ax.get_yaxis_transform(),
                ha="left", va="center", fontsize=8.5, fontweight="bold",
                color=INK)
        ax.text(thr, y_head, gthr, ha="center", va="center", fontsize=7.5,
                color=INK)
        y -= GAP_H

    y_bottom = y + GAP_H
    ax.set_ylim(y_bottom - 0.2, 0.6)
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticks(ticks_y)
    ax.set_yticklabels(ticks_label, fontsize=8)
    ax.tick_params(axis="y", length=0, pad=52)
    ax.set_xlabel("Evaluation score (proportion)", fontsize=8.5)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.xaxis.grid(True, color=LIGHTGREY, lw=0.5, ls=(0, (1, 3)), zorder=0)
    ax.set_axisbelow(True)

    # Column header for the posterior column.
    ax.text(1.02, 0.6, r"$P(\theta > \tau)$", transform=ax.get_yaxis_transform(),
            ha="left", va="center", fontsize=7.5, color=GREY, style="italic")

    legend_handles = [
        Line2D([], [], color=BLUE, lw=2.2, marker="o", ms=6,
               markerfacecolor=BLUE, markeredgecolor=BLUE,
               label="resolved: one-sided 95% bound clears threshold"),
        Line2D([], [], color=VERMILION, lw=2.2, marker="o", ms=6,
               markerfacecolor="white", markeredgecolor=VERMILION,
               markeredgewidth=1.4,
               label="cannot resolve: one-sided 95% bound reaches threshold"),
        Line2D([], [], color=INK, lw=1.4, marker="|", ms=0, ls="-",
               label=r"decision threshold $\tau$"),
        Line2D([], [], color=GREY, lw=0.9,
               label="one-sided 95% bounds under clustering (ICC = 0.2)"),
    ]
    ax.legend(handles=legend_handles, loc="upper center",
              bbox_to_anchor=(0.42, -0.10), ncol=2, frameon=False,
              fontsize=7.5, handlelength=1.8, columnspacing=1.6,
              borderaxespad=0)

    fig.subplots_adjust(left=0.26, right=0.90, top=0.97, bottom=0.20)

    outdir = ROOT / "paper/figures"
    outdir.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        out = outdir / f"ci_straddle.{ext}"
        fig.savefig(out, dpi=300)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
