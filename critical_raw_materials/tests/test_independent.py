"""Recompute the main numbers a second way, with the standard library only
(no pandas, no project code), and compare with the pipeline."""
import csv
from collections import defaultdict

import pytest

import config as C
from src.load import load
from src.metrics import hhi, shares, supplier_values, yearly_table

EU = {"AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT",
      "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"}
NOT_COUNTRIES = {"EXT_EU27_2020", "INT_EU27_2020", "QV", "QW", "QY", "QZ"}


def raw_rows():
    with open(C.DATA_FILE, newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)


def independent(material_codes, years, indicator="VALUE_IN_EUROS"):
    by_country = defaultdict(float)
    for r in raw_rows():
        if (r["product"] in material_codes and int(r["TIME_PERIOD"]) in years
                and r["indicators"] == indicator
                and r["partner"] not in EU and r["partner"] not in NOT_COUNTRIES):
            by_country[r["partner"]] += float(r["OBS_VALUE"])
    total = sum(by_country.values())
    h = sum((100 * v / total) ** 2 for v in by_country.values())
    return h, by_country.get("CN", 0) / total, by_country


@pytest.fixture(scope="module")
def data():
    return load(C.DATA_FILE)[0]


@pytest.mark.parametrize("material", list(C.MATERIALS))
@pytest.mark.parametrize("indicator", ["VALUE_IN_EUROS", "QUANTITY_IN_100KG"])
def test_baseline_hhi_and_china_share(data, material, indicator):
    years = range(2023, 2026)
    h_ind, cn_ind, _ = independent(set(C.MATERIALS[material]), set(years), indicator)
    vals, _ = supplier_values(data, indicator, material, years)
    s = shares(vals)
    assert hhi(s) == pytest.approx(h_ind, rel=1e-9)
    assert s.get("CN", 0) == pytest.approx(cn_ind, rel=1e-9)


def test_every_year_matches(data):
    table = yearly_table(data, "VALUE_IN_EUROS")
    for r in table.itertuples():
        h_ind, cn_ind, _ = independent(set(C.MATERIALS[r.material]), {r.year})
        assert r.hhi == pytest.approx(h_ind, rel=1e-9), (r.material, r.year)
        assert r.china_share == pytest.approx(cn_ind, rel=1e-9, abs=1e-12)


def test_namibia_counts_as_a_supplier(data):
    _, _, by_country = independent(set(C.MATERIALS["Natural graphite"]), set(range(2010, 2026)))
    vals, _ = supplier_values(data, "VALUE_IN_EUROS", "Natural graphite", range(2010, 2026))
    assert by_country.get("NA", 0) == pytest.approx(vals.get("NA", 0))


def test_values_copied_from_the_raw_file(data):
    # Lines read by eye in the Eurostat file
    def v(partner, product, year):
        d = data[(data.partner == partner) & (data["product"] == product)
                 & (data.year == year) & (data.indicator == "VALUE_IN_EUROS")]
        return d["value"].iloc[0]
    assert v("CN", "283691", 2023) == 32_897_038
    assert v("CL", "283691", 2022) == 268_131_457
    assert v("AU", "282520", 2025) == 9_721_559
    assert v("CD", "810520", 2014) == 181_604_209
