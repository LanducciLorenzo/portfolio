"""Load and validate the Eurostat Comext export (DS-045409, SDMX-CSV).

Two traps handled here:
* The partner code for Namibia is "NA". Default CSV readers turn it into a
  missing value, so the file is read with keep_default_na=False.
* A file copied and pasted from the browser can be cut off mid-line. Every row
  is checked, and the file is refused if any row is incomplete.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

import config as C


class DataError(ValueError):
    """The data file is not what the analysis expects."""


def read_raw(path: Path | str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    missing = [c for c in C.EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise DataError(f"Missing columns: {missing}. Is this an SDMX-CSV export of DS-045409?")
    # Fields missing at the end of a cut-off row come back as NaN: make them "".
    df = df.fillna("")
    for col in C.EXPECTED_COLUMNS:
        df[col] = df[col].astype(str).str.strip()
    return df


def validate(df: pd.DataFrame) -> list[str]:
    """Return a list of problems; an empty list means the file passed."""
    problems = []
    empty = (df[C.EXPECTED_COLUMNS] == "").any(axis=1)
    if empty.any():
        problems.append(f"{empty.sum()} row(s) with empty fields (file cut off?), "
                        f"first at data row {int(empty.idxmax()) + 1}")
    values = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    bad = values.isna() & ~empty
    if bad.any():
        problems.append(f"{bad.sum()} non-numeric value(s), e.g. {df.loc[bad, 'OBS_VALUE'].iloc[0]!r}")
    if (values < 0).any():
        problems.append(f"{(values < 0).sum()} negative value(s)")
    years = pd.to_numeric(df.loc[~empty, "TIME_PERIOD"], errors="coerce")
    if years.isna().any() or ((years < 1988) | (years > 2100)).any():
        problems.append("TIME_PERIOD contains values that are not years (monthly data?)")
    for col, expected in [("reporter", C.REPORTER), ("flow", C.FLOW_IMPORTS), ("freq", C.FREQ_ANNUAL)]:
        found = set(df.loc[~empty, col].unique())
        if found != {expected}:
            problems.append(f"Column {col!r} should be only {expected!r}, found {sorted(found)}")
    key = ["partner", "product", "indicators", "TIME_PERIOD"]
    dups = df.duplicated(key)
    if dups.any():
        problems.append(f"{dups.sum()} duplicated partner/product/indicator/year row(s)")
    return problems


def tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Keep the useful columns, add the material, convert types."""
    code_to_material = {code: mat for mat, codes in C.MATERIALS.items() for code in codes}
    out = pd.DataFrame({
        "partner": df["partner"],
        "product": df["product"],
        "indicator": df["indicators"],
        "year": df["TIME_PERIOD"].astype(int),
        "value": df["OBS_VALUE"].astype(float),
    })
    unknown = sorted(set(out["product"]) - set(code_to_material))
    if unknown:
        raise DataError(f"Product codes not in config.MATERIALS: {unknown}")
    out["material"] = out["product"].map(code_to_material)
    return out


def partner_type(code: str) -> str:
    if code in (C.AGG_EXTRA, C.AGG_INTRA):
        return "aggregate"
    if code in C.EU27:
        return "intra_eu"
    if code in C.UNATTRIBUTED_INTRA:
        return "unattributed_intra"
    if code in C.UNATTRIBUTED_EXTRA:
        return "unattributed_extra"
    return "extra_eu"


def reconcile(tidy_df: pd.DataFrame, tolerance: float = 1.0) -> pd.DataFrame:
    """Check that country rows add up to Eurostat's own totals.

    For every product, indicator and year:
      extra-EU countries + unattributed extra-EU  ==  EXT_EU27_2020
      EU member states   + unattributed intra-EU  ==  INT_EU27_2020
    Returns the rows that do not match (empty = all good).
    """
    d = tidy_df.assign(ptype=tidy_df["partner"].map(partner_type))
    key = ["product", "indicator", "year"]
    totals = d[d["ptype"] == "aggregate"].pivot_table(
        index=key, columns="partner", values="value", aggfunc="sum").fillna(0)
    extra = d[d["ptype"].isin(["extra_eu", "unattributed_extra"])].groupby(key)["value"].sum()
    intra = d[d["ptype"].isin(["intra_eu", "unattributed_intra"])].groupby(key)["value"].sum()
    check = pd.DataFrame({
        "eurostat_extra": totals.get(C.AGG_EXTRA, pd.Series(dtype=float)),
        "sum_extra": extra,
        "eurostat_intra": totals.get(C.AGG_INTRA, pd.Series(dtype=float)),
        "sum_intra": intra,
    }).fillna(0)
    bad = ((check["eurostat_extra"] - check["sum_extra"]).abs() > tolerance) | \
          ((check["eurostat_intra"] - check["sum_intra"]).abs() > tolerance)
    return check[bad]


def load(path: Path | str = C.DATA_FILE) -> tuple[pd.DataFrame, dict]:
    """Read, validate, reconcile. Returns tidy data and a small audit dict."""
    raw = read_raw(path)
    problems = validate(raw)
    if problems:
        raise DataError("The data file did not pass the checks:\n- " + "\n- ".join(problems))
    data = tidy(raw)
    mismatches = reconcile(data)
    audit = {
        "rows": len(raw),
        "last_update": sorted(raw["LAST UPDATE"].unique()),
        "years": (int(data["year"].min()), int(data["year"].max())),
        "products": sorted(data["product"].unique()),
        "indicators": sorted(data["indicator"].unique()),
        "partners": int(data["partner"].nunique()),
        "reconciliation_mismatches": len(mismatches),
        "reconciliation_checked": int(data[data["partner"].isin([C.AGG_EXTRA, C.AGG_INTRA])]
                                      .groupby(["product", "indicator", "year"]).ngroups),
    }
    if len(mismatches):
        raise DataError(f"Country rows do not add up to Eurostat totals in {len(mismatches)} case(s):\n"
                        f"{mismatches.head()}")
    return data, audit
