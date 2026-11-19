"""Figures (static PNG, matplotlib)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

import config as C  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
OTHER = "#b9b8b2"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "text.color": INK, "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
})


def _materials(table: pd.DataFrame) -> list[str]:
    return [m for m in C.MATERIALS if m in set(table["material"])]


def small_multiples(table: pd.DataFrame, column: str, title: str, ylabel: str,
                    ref: float | None, ref_label: str, path, percent: bool) -> None:
    mats = _materials(table)
    fig, axes = plt.subplots(1, len(mats), figsize=(3.1 * len(mats), 3.4), sharey=True)
    for ax, mat in zip(axes, mats):
        d = table[table["material"] == mat].sort_values("year")
        y = d[column] * (100 if percent else 1)
        ax.plot(d["year"], y, color=BLUE, linewidth=2, marker="o", markersize=4,
                markeredgecolor=SURFACE, markeredgewidth=1)
        if ref is not None:
            ax.axhline(ref, color=INK_2, linewidth=1, linestyle=(0, (4, 3)))
        ax.set_title(mat)
        ax.set_xticks([2010, 2015, 2020, 2025])
        ax.tick_params(length=0)
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel(ylabel)
    if ref is not None:
        axes[-1].annotate(ref_label, xy=(1, ref), xycoords=("axes fraction", "data"),
                          xytext=(0, 4), textcoords="offset points", ha="right", va="bottom",
                          fontsize=8, color=INK_2)
    upper = 100 if percent else 10_000
    axes[0].set_ylim(0, upper * 1.02)
    fig.suptitle(title, x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def supplier_bars(baseline: dict[str, pd.Series], years_label: str, path) -> None:
    """100% horizontal bars: China, Australia, largest other supplier, all others."""
    mats = list(baseline)
    fig, ax = plt.subplots(figsize=(9.5, 0.75 * len(mats) + 1.6))
    for i, mat in enumerate(mats):
        s = baseline[mat]
        cn, au = float(s.get("CN", 0)), float(s.get("AU", 0))
        rest = s.drop([c for c in ("CN", "AU") if c in s.index])
        top_code = rest.index[0] if len(rest) else None
        top = float(rest.iloc[0]) if len(rest) else 0.0
        others = 1 - cn - au - top
        top_name = C.COUNTRY_NAMES.get(top_code, top_code) if top_code else ""
        segs = [("China", cn, BLUE), ("Australia", au, ORANGE),
                (f"{top_name}", top, AQUA), ("All others", others, OTHER)]
        left = 0.0
        for label, w, color in segs:
            if w <= 0:
                continue
            ax.barh(i, w * 100, left=left * 100, color=color, height=0.6,
                    edgecolor=SURFACE, linewidth=2)
            txt = f"{label} {w:.0%}"
            if w * 100 < len(txt) * 0.95 + 2:      # text would not fit: percent only
                txt = f"{w:.0%}"
            if w * 100 >= len(txt) * 0.95 + 2:
                ax.text((left + w / 2) * 100, i, txt, ha="center", va="center", fontsize=8.5,
                        color="white" if color in (BLUE,) else INK)
            left += w
    ax.set_axisbelow(True)
    ax.set_yticks(range(len(mats)), mats)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of attributable extra-EU imports (%), by value")
    ax.grid(axis="y", visible=False)
    ax.tick_params(length=0)
    from matplotlib.patches import Patch
    handles = [Patch(color=BLUE, label="China"), Patch(color=ORANGE, label="Australia"),
               Patch(color=AQUA, label="Largest other supplier"),
               Patch(color=OTHER, label="All other suppliers")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=4,
              frameon=False, fontsize=8.5)
    ax.set_title(f"Who supplies the EU? Average {years_label}", loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def scenario_plot(scen: pd.DataFrame, path) -> None:
    mats = [m for m in C.MATERIALS if m in set(scen["material"])]
    fig, axes = plt.subplots(1, len(mats), figsize=(3.1 * len(mats), 3.4), sharey=True)
    for ax, mat in zip(axes, mats):
        d = scen[scen["material"] == mat].sort_values("shift")
        ax.plot(d["shift"] * 100, d["hhi"], color=BLUE, linewidth=2, marker="o", markersize=5,
                markeredgecolor=SURFACE, markeredgewidth=1)
        ax.axhline(C.HHI_HIGH, color=INK_2, linewidth=1, linestyle=(0, (4, 3)))
        ax.set_title(mat)
        ax.set_xticks([s * 100 for s in C.SCENARIO_SHIFTS])
        ax.set_xlabel("% of China's supply\nmoved to Australia")
        ax.tick_params(length=0)
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("HHI (0-10,000)")
    axes[0].set_ylim(0, 10_200)
    axes[-1].annotate(f"{C.HHI_HIGH:,}: 'highly concentrated'", xy=(1, C.HHI_HIGH),
                      xycoords=("axes fraction", "data"), xytext=(0, 4), textcoords="offset points",
                      ha="right", va="bottom", fontsize=8, color=INK_2)
    fig.suptitle("Scenario: concentration if part of China's supply came from Australia",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
