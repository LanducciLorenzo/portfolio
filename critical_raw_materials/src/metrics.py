"""Supplier shares and concentration (Herfindahl-Hirschman index).

All shares are shares of the EU's *extra-EU* imports that can be attributed
to a country. Confidential or unspecified partners (Comext codes QW, QZ) are
left out of the shares and reported separately.
"""
from __future__ import annotations

import pandas as pd

import config as C
from src.load import partner_type


def extra_eu(data: pd.DataFrame, indicator: str) -> pd.DataFrame:
    """Extra-EU rows for one indicator, with a column marking unattributed partners."""
    d = data[data["indicator"] == indicator].copy()
    d["ptype"] = d["partner"].map(partner_type)
    d = d[d["ptype"].isin(["extra_eu", "unattributed_extra"])]
    return d


def supplier_values(data: pd.DataFrame, indicator: str, material: str,
                    years: list[int] | range) -> tuple[pd.Series, float]:
    """Imports by partner country, summed over the material's products and the years.

    Returns (values by attributable country, unattributed amount).
    """
    d = extra_eu(data, indicator)
    d = d[(d["material"] == material) & (d["year"].isin(list(years)))]
    unattributed = float(d.loc[d["ptype"] == "unattributed_extra", "value"].sum())
    by_partner = d[d["ptype"] == "extra_eu"].groupby("partner")["value"].sum()
    by_partner = by_partner[by_partner > 0].sort_values(ascending=False)
    return by_partner, unattributed


def shares(values: pd.Series) -> pd.Series:
    total = values.sum()
    if total <= 0:
        raise ValueError("No imports to compute shares from")
    return values / total


def hhi(share: pd.Series) -> float:
    """Herfindahl-Hirschman index on the 0-10,000 scale (shares in percent, squared, summed)."""
    s = share[share > 0]
    if abs(s.sum() - 1) > 1e-9:
        raise ValueError(f"Shares must add up to 1, got {s.sum():.6f}")
    return float(((100 * s) ** 2).sum())


def equivalent_suppliers(h: float) -> float:
    """10,000 / HHI: the number of equal-sized suppliers giving the same concentration."""
    return 10_000 / h


def yearly_table(data: pd.DataFrame, indicator: str) -> pd.DataFrame:
    """One row per material and year with the main indicators."""
    rows = []
    d = extra_eu(data, indicator)
    for material in [m for m in C.MATERIALS if m in set(d["material"])]:
        for year in sorted(d.loc[d["material"] == material, "year"].unique()):
            vals, unatt = supplier_values(data, indicator, material, [year])
            if vals.sum() <= 0:
                continue
            s = shares(vals)
            h = hhi(s)
            total = vals.sum() + unatt
            rows.append({
                "material": material,
                "year": int(year),
                "extra_eu_total": total,
                "unattributed_share": unatt / total,
                "n_suppliers": int((s > 0).sum()),
                "hhi": h,
                "equivalent_suppliers": equivalent_suppliers(h),
                "top_supplier": s.index[0],
                "top_share": float(s.iloc[0]),
                "china_share": float(s.get("CN", 0.0)),
                "australia_share": float(s.get("AU", 0.0)),
            })
    return pd.DataFrame(rows)


def products_found(data: pd.DataFrame) -> dict[str, list[str]]:
    found = set(data["product"])
    return {m: [c for c in codes if c in found] for m, codes in C.MATERIALS.items()}
