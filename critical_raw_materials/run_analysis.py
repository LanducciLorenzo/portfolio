"""How concentrated are the EU's imports of critical raw materials, and how much
could more supply from Australia change that?

Run:  python run_analysis.py
Input: data/eurostat_raw.csv (Eurostat Comext DS-045409, SDMX-CSV export)
Output: results/report.md, results/*.csv, results/figures/*.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config as C  # noqa: E402
from src import figures  # noqa: E402
from src.load import load  # noqa: E402
from src.metrics import (equivalent_suppliers, hhi, products_found, shares,  # noqa: E402
                         supplier_values, yearly_table)
from src.scenario import shift, shift_for_hhi, shift_for_max_share  # noqa: E402

VALUE, QTY = "VALUE_IN_EUROS", "QUANTITY_IN_100KG"
CRMA_LIMIT = 0.65


def name(code: str) -> str:
    return C.COUNTRY_NAMES.get(code, code)


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def concentration_label(h: float) -> str:
    return "highly concentrated" if h > C.HHI_HIGH else "not highly concentrated"


def main() -> None:
    C.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    data, audit = load(C.DATA_FILE)
    found = products_found(data)
    materials = [m for m, codes in found.items() if codes]
    has_qty = QTY in audit["indicators"]

    y_first, y_last = audit["years"]
    base_years = list(range(y_last - C.BASELINE_YEARS + 1, y_last + 1))
    start_years = list(range(y_first, y_first + C.BASELINE_YEARS))
    base_label = f"{base_years[0]}-{base_years[-1]}"
    start_label = f"{start_years[0]}-{start_years[-1]}"

    # ---- yearly indicators -------------------------------------------------
    yv = yearly_table(data, VALUE)
    yv.to_csv(C.RESULTS_DIR / "yearly_by_value.csv", index=False)
    if has_qty:
        yq = yearly_table(data, QTY)
        yq.to_csv(C.RESULTS_DIR / "yearly_by_quantity.csv", index=False)

    # ---- baseline (average of the last years) ------------------------------
    base_rows, baseline_shares, scen_rows, needs = [], {}, [], []
    for mat in materials:
        vals, unatt = supplier_values(data, VALUE, mat, base_years)
        s = shares(vals)
        baseline_shares[mat] = s
        h = hhi(s)
        start_vals, _ = supplier_values(data, VALUE, mat, start_years)
        s_start = shares(start_vals)
        row = {
            "Material": mat,
            "Imports (EUR m/yr)": f"{(vals.sum() + unatt) / len(base_years) / 1e6:,.0f}",
            "Suppliers": int((s > 0).sum()),
            "HHI": f"{h:,.0f}",
            "Equivalent suppliers": f"{equivalent_suppliers(h):.1f}",
            "Largest supplier": f"{name(s.index[0])} ({pct(s.iloc[0])})",
            f"China {start_label}": pct(s_start.get("CN", 0)),
            f"China {base_label}": pct(s.get("CN", 0)),
            f"Australia {base_label}": pct(s.get("AU", 0)),
        }
        if has_qty:
            qv, _ = supplier_values(data, QTY, mat, base_years)
            sq = shares(qv)
            row["HHI by quantity"] = f"{hhi(sq):,.0f}"
            row["China by quantity"] = pct(sq.get("CN", 0))
        base_rows.append(row)

        for sh in C.SCENARIO_SHIFTS:
            s2 = shift(s, sh)
            leaders = [c for c in s2.index if abs(s2[c] - s2.iloc[0]) < 1e-9]
            scen_rows.append({
                "material": mat, "shift": sh, "hhi": hhi(s2),
                "china_share": float(s2.get("CN", 0)), "australia_share": float(s2.get("AU", 0)),
                "largest_supplier": "+".join(sorted(leaders)), "largest_share": float(s2.iloc[0]),
            })
        needs.append({
            "Material": mat,
            "China share now": pct(s.get("CN", 0)),
            "Largest single supplier": f"{name(s.index[0])} ({pct(s.iloc[0])})",
            "Above 65%?": "yes" if s.iloc[0] > CRMA_LIMIT else "no",
            "Shift needed for China <= 65%": _fmt_shift(shift_for_max_share(s, CRMA_LIMIT)),
            f"Shift needed for HHI <= {C.HHI_HIGH:,}": _fmt_shift(shift_for_hhi(s, C.HHI_HIGH)),
        })

    base_df = pd.DataFrame(base_rows)
    base_df.to_csv(C.RESULTS_DIR / "baseline.csv", index=False)
    scen = pd.DataFrame(scen_rows)
    scen.to_csv(C.RESULTS_DIR / "scenario.csv", index=False)
    needs_df = pd.DataFrame(needs)

    # top suppliers per material, for the appendix
    top_rows = []
    for mat, s in baseline_shares.items():
        for rank, (code, sh) in enumerate(s.head(5).items(), start=1):
            top_rows.append({"material": mat, "rank": rank, "partner": code,
                             "country": name(code), "share": sh})
    top_df = pd.DataFrame(top_rows)
    top_df.to_csv(C.RESULTS_DIR / "top_suppliers_baseline.csv", index=False)

    # ---- figures -------------------------------------------------------------
    figures.small_multiples(yv, "china_share", "China's share of EU imports from outside the EU, by value",
                            "China's share (%)", 65, "65%: CRMA benchmark (on consumption)",
                            C.FIGURES_DIR / "china_share.png", percent=True)
    figures.small_multiples(yv, "hhi", "Concentration of EU suppliers outside the EU (HHI), by value",
                            "HHI (0-10,000)", C.HHI_HIGH, f"{C.HHI_HIGH:,}: 'highly concentrated'",
                            C.FIGURES_DIR / "hhi.png", percent=False)
    figures.supplier_bars(baseline_shares, base_label, C.FIGURES_DIR / "suppliers_baseline.png")
    figures.scenario_plot(scen, C.FIGURES_DIR / "scenario.png")

    # ---- report --------------------------------------------------------------
    flagged = yv[yv["unattributed_share"] > C.UNATTRIBUTED_WARN]
    scen_show = scen.copy()
    scen_show["shift"] = (scen_show["shift"] * 100).round().astype(int).astype(str) + "%"
    scen_show["hhi"] = scen_show["hhi"].map(lambda x: f"{x:,.0f}")
    for c in ("china_share", "australia_share", "largest_share"):
        scen_show[c] = scen_show[c].map(pct)
    scen_show["largest_supplier"] = scen_show["largest_supplier"].map(
        lambda codes: " = ".join(name(c) for c in codes.split("+")) + (" (tie)" if "+" in codes else ""))
    scen_show.columns = ["Material", "Shift", "HHI", "China", "Australia",
                         "Largest supplier", "Largest share"]

    findings = []
    for mat in materials:
        s = baseline_shares[mat]
        start_vals, _ = supplier_values(data, VALUE, mat, start_years)
        cn0 = shares(start_vals).get("CN", 0)
        h = hhi(s)
        largest = ("China is the largest supplier" if s.index[0] == "CN"
                   else f"the largest supplier is {name(s.index[0])} ({pct(s.iloc[0])})")
        line = (f"- **{mat}**: China supplies {pct(s.get('CN', 0))} of attributable extra-EU imports "
                f"in {base_label} (vs {pct(cn0)} in {start_label})")
        if has_qty:
            q0, _ = supplier_values(data, QTY, mat, start_years)
            q1, _ = supplier_values(data, QTY, mat, base_years)
            line += (f"; by quantity {pct(shares(q1).get('CN', 0))} "
                     f"(vs {pct(shares(q0).get('CN', 0))})")
        line += (f". {largest[0].upper() + largest[1:]}. HHI {h:,.0f} ({concentration_label(h)}), "
                 f"like {equivalent_suppliers(h):.1f} equal-sized suppliers. "
                 f"Australia: {pct(s.get('AU', 0))}.")
        findings.append(line)
        if has_qty:
            hq = hhi(shares(q1))
            if (hq > C.HHI_HIGH) != (h > C.HHI_HIGH):
                findings.append(
                    f"  - Check: by quantity the picture differs (HHI {hq:,.0f}), "
                    f"so the concentration verdict for {mat.lower()} depends on the measure.")

    codes_text = "\n".join(
        f"  - {mat}: " + ", ".join(f"{c} ({C.MATERIALS[mat][c]})" for c in codes)
        for mat, codes in found.items() if codes)
    missing = [f"{c} ({mat})" for mat, codes in C.MATERIALS.items() for c in codes
               if c not in found[mat]]

    report = f"""# EU dependence on critical raw materials: supplier concentration and an Australia scenario

*Generated by `run_analysis.py` from Eurostat data (last update {", ".join(audit["last_update"])}).*

## Question

How dependent is the EU on a small number of non-EU suppliers for critical raw materials,
how has China's role changed since {y_first}, and how much would concentration fall if part
of China's supply came from Australia instead (for example, as a result of the EU-Australia
free trade agreement)?

## Data

- Source: Eurostat Comext, dataset DS-045409 (EU trade by HS6/CN8), annual, reporter EU27_2020
  (the current 27 members, applied to all years), imports, {y_first}-{y_last}.
- Indicators: {", ".join(audit["indicators"])}.
- Products (HS 6-digit), grouped into materials:
{codes_text}
{"- Not in the data file: " + ", ".join(missing) if missing else ""}

Only imports from **outside the EU** are used. Partners that Eurostat reports as confidential or
not specified (codes QW, QZ) are excluded from the shares and reported separately.

## Data checks

- {audit["rows"]:,} rows read; no empty, non-numeric, negative or duplicated values.
- For every product, indicator and year ({audit["reconciliation_checked"]} combinations), the country rows add up
  exactly to Eurostat's own extra-EU and intra-EU totals ({audit["reconciliation_mismatches"]} mismatches).
- Material-years where more than {C.UNATTRIBUTED_WARN:.0%} of extra-EU imports are confidential or unattributed:
  {", ".join(f"{r.material} {r.year} ({pct(r.unattributed_share)})" for r in flagged.itertuples()) or "none"}.

## Key findings

{chr(10).join(findings)}

## Baseline: average {base_label}, by value

HHI = sum of squared percentage shares (0-10,000). "Equivalent suppliers" = 10,000 / HHI.
For reference, the 2023 US Merger Guidelines call a market highly concentrated above {C.HHI_HIGH:,}.

{md_table(base_df)}

![Suppliers](figures/suppliers_baseline.png)

## Trends {y_first}-{y_last}

![China's share](figures/china_share.png)

![HHI](figures/hhi.png)

Full yearly tables: `yearly_by_value.csv`{", `yearly_by_quantity.csv`" if has_qty else ""}.

## Scenario: part of China's supply comes from Australia

Mechanical what-if on the {base_label} shares: a fraction of China's imports is reassigned to
Australia, total imports unchanged. It is not a forecast and says nothing about whether
Australian producers could supply these quantities, at what price, or in which processed form.

{md_table(scen_show)}

![Scenario](figures/scenario.png)

### Distance from the benchmarks

The Critical Raw Materials Act (Regulation (EU) 2024/1252) aims for no single third country to
provide more than 65% of EU consumption of each strategic raw material by 2030. Consumption is not
the same as extra-EU imports, so the comparison below is only indicative.

{md_table(needs_df)}

"—" means the target cannot be reached by moving supply from China to Australia alone.

## How to read these results (limitations)

1. **Imports are not consumption.** EU production, recycling and stocks are not included, and goods
   can be re-exported after import.
2. **Country of origin is the last processing country.** For example, rare-earth compounds refined
   in Malaysia count as Malaysian even if the ore was mined elsewhere. Upstream dependence can be
   larger or smaller than these shares suggest.
3. **Values move with prices.** Lithium prices rose sharply in 2022 and fell afterwards; quantity-based
   indicators are shown as a check.
4. **Quantities add different compounds** (e.g. lithium carbonate and hydroxide) by weight, not by
   metal content.
5. **HS6 codes are broad** for some materials (e.g. permanent magnets of metal include non-rare-earth
   magnets).
6. **The scenario is arithmetic**, not an economic model of trade diversion.
"""
    (C.RESULTS_DIR / "report.md").write_text(report, encoding="utf-8")
    print(f"Done. Report: {C.RESULTS_DIR / 'report.md'}")


def _fmt_shift(x: float | None) -> str:
    if x is None:
        return "—"
    if x == 0:
        return "already met"
    return f"{100 * x:.0f}%"


if __name__ == "__main__":
    main()
