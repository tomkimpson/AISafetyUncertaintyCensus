#!/usr/bin/env python
"""Companion figure for the bio-uplift case study: the uplift-ratio interval
against the acceptable-risk line, under every admissible reading of ``±13%``.

The headline proportion figure (``scripts/make_figure.py``) covers the nine
proportion-audit rows but not the uplift trial, whose score is a ratio of means.
This puts the paper's central case in front of the reader: a forest plot of the
Fieller 95% set for each reading of the card's unlabelled ``±13%`` against the
2.8x acceptable line and the 5x significant-risk line. Every reading straddles
2.8x; the SD reading (the most conventional) is bounded and also excludes 5x;
the SE reading is unbounded above (conditional on that reading), drawn with an
arrow. Reads data/derived/uplift_readings.csv (from uplift_analysis.py) and
writes paper/figures/uplift_straddle.{pdf,png}.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyArrow  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# Okabe-Ito, matching make_figure.py.
BLUE = "#0072B2"
VERMILION = "#D55E00"
INK = "#1a1a1a"
GREY = "#999999"
LIGHTGREY = "#c8c8c8"

ACCEPTABLE = 2.8   # tau: <= keeps risk acceptable
SIGNIF = 5.0       # >= creates significant additional risk
POINT = 2.53       # card's reported uplift (unrounded means)
XMAX = 6.2         # right edge of the ratio axis

# Rows top-to-bottom: lead with the robust, bounded SD reading; the SE reading
# (unbounded) sits last as the extreme end of the envelope. Each entry selects
# the headline Fieller method for that reading.
ROWS = [
    ("SD", "8", "fieller_t", "SD reading, $n=8$"),
    ("SD", "9", "fieller_t", "SD reading, $n=9$"),
    ("SD", "10", "fieller_t", "SD reading, $n=10$"),
    ("CI half-width", "n-free", "fieller_z", "CI-half-width reading"),
    ("SE", "n-free", "fieller_z", "SE reading"),
]


def _num(x):
    if x in ("+inf", "inf"):
        return math.inf
    if x in ("-inf",):
        return -math.inf
    return float(x)


def load():
    src = ROOT / "data/derived/uplift_readings.csv"
    if not src.exists():
        sys.exit("run scripts/uplift_analysis.py first")
    rows = list(csv.DictReader(src.open()))
    keyed = {(r["reading"], r["arm_n"], r["method"]): r for r in rows}
    return keyed


def main():
    keyed = load()

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 8,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })

    n = len(ROWS)
    fig, ax = plt.subplots(figsize=(7.2, 0.52 * n + 1.5))

    ys = list(range(n, 0, -1))  # top row highest y
    ylabels = []
    for y, (reading, arm, method, label) in zip(ys, ROWS):
        r = keyed[(reading, arm, method)]
        lo = _num(r["low"])
        hi = _num(r["high"])
        ylabels.append(label)
        unbounded = math.isinf(hi)
        hi_draw = XMAX if unbounded else hi

        # every reading straddles 2.8x -> vermilion "cannot resolve" encoding
        ax.plot([lo, hi_draw], [y, y], color=VERMILION, lw=2.4,
                solid_capstyle="butt", zorder=3)
        # end caps (left cap always; right cap only if bounded)
        ax.plot([lo, lo], [y - 0.16, y + 0.16], color=VERMILION, lw=1.6, zorder=3)
        if not unbounded:
            ax.plot([hi, hi], [y - 0.16, y + 0.16], color=VERMILION, lw=1.6,
                    zorder=3)
        else:
            ax.add_patch(FancyArrow(
                XMAX - 0.35, y, 0.33, 0, width=0.0, head_width=0.20,
                head_length=0.18, length_includes_head=True, color=VERMILION,
                zorder=3))
            ax.text(XMAX, y + 0.28, r"unbounded above", ha="right", va="bottom",
                    fontsize=6.8, color=VERMILION, style="italic")
        # point estimate (open marker, matching the "cannot resolve" style)
        ax.plot(POINT, y, marker="o", ms=6, zorder=4, markerfacecolor="white",
                markeredgecolor=VERMILION, markeredgewidth=1.4)

    # threshold lines
    ax.axvline(ACCEPTABLE, color=INK, lw=1.4, zorder=2)
    ax.axvline(SIGNIF, color=GREY, lw=1.2, ls=(0, (4, 2)), zorder=2)
    ax.text(ACCEPTABLE, n + 0.62, r"$2.8\times$ acceptable line", ha="center",
            va="bottom", fontsize=7.5, color=INK)
    ax.text(SIGNIF, n + 0.62, r"$5\times$ significant-risk line", ha="center",
            va="bottom", fontsize=7.5, color=GREY)

    ax.set_ylim(0.4, n + 1.2)
    ax.set_xlim(0.8, XMAX + 0.05)
    ax.set_xticks([1, 2, 3, 4, 5, 6])
    ax.set_xticklabels([r"$1\times$", r"$2\times$", r"$3\times$", r"$4\times$",
                        r"$5\times$", r"$6\times$"])
    ax.set_yticks(ys)
    ax.set_yticklabels(ylabels, fontsize=8)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Uplift ratio (Opus-4 arm mean / control arm mean)", fontsize=8.5)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.xaxis.grid(True, color=LIGHTGREY, lw=0.5, ls=(0, (1, 3)), zorder=0)
    ax.set_axisbelow(True)

    legend_handles = [
        Line2D([], [], color=VERMILION, lw=2.4, marker="o", ms=6,
               markerfacecolor="white", markeredgecolor=VERMILION,
               markeredgewidth=1.4,
               label=r"Fieller 95% set (point $=2.53\times$); straddles $2.8\times$"),
        Line2D([], [], color=INK, lw=1.4, label=r"$2.8\times$ acceptable line"),
        Line2D([], [], color=GREY, lw=1.2, ls=(0, (4, 2)),
               label=r"$5\times$ significant-risk line"),
    ]
    ax.legend(handles=legend_handles, loc="upper center",
              bbox_to_anchor=(0.5, -0.16), ncol=1, frameon=False, fontsize=7.5,
              handlelength=1.8, borderaxespad=0)

    fig.subplots_adjust(left=0.24, right=0.97, top=0.86, bottom=0.30)

    outdir = ROOT / "paper/figures"
    outdir.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        out = outdir / f"uplift_straddle.{ext}"
        fig.savefig(out, dpi=300)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
