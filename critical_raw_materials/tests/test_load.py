"""Tests for reading and checking the Eurostat file."""
import pandas as pd
import pytest

import config as C
from src.load import DataError, load, read_raw, reconcile, tidy, validate

HEADER = ",".join(C.EXPECTED_COLUMNS)


def row(partner, product="283691", value="100", year="2024", indicator="VALUE_IN_EUROS",
        flow="1", freq="A", reporter="EU27_2020"):
    return (f"ESTAT:DS-045409(1.0),13/11/26 11:00:00,{freq},{reporter},{partner},{product},"
            f"{flow},{indicator},{year},{value}")


def write(tmp_path, lines, name="data.csv"):
    p = tmp_path / name
    p.write_text("\n".join([HEADER] + lines) + "\n", encoding="utf-8")
    return p


def balanced(extra=None):
    """A tiny file whose country rows add up to the Eurostat totals."""
    lines = [row("CN", value="60"), row("NA", value="30"), row("QZ", value="10"),
             row("DE", value="50"), row("EXT_EU27_2020", value="100"),
             row("INT_EU27_2020", value="50")]
    return lines + (extra or [])


def test_namibia_is_not_read_as_missing(tmp_path):
    data, audit = load(write(tmp_path, balanced()))
    assert "NA" in set(data["partner"])
    assert audit["reconciliation_mismatches"] == 0


def test_real_snippet_reads(tmp_path):
    df = read_raw("tests/fixtures/real_snippet.csv")
    assert validate(df) == []
    d = tidy(df)
    v = d[(d.partner == "CL") & (d["product"] == "283691") & (d.year == 2023)]["value"]
    assert v.iloc[0] == 173_256_696


def test_cut_off_file_is_refused(tmp_path):
    lines = balanced()
    lines[-1] = lines[-1][:40]          # the last line is cut in the middle
    with pytest.raises(DataError, match="empty fields"):
        load(write(tmp_path, lines))


def test_windows_line_endings_are_fine(tmp_path):
    p = tmp_path / "crlf.csv"
    p.write_bytes(("\r\n".join([HEADER] + balanced()) + "\r\n").encode())
    data, _ = load(p)
    assert data["value"].sum() == 300


@pytest.mark.parametrize("bad, message", [
    (row("US", flow="2"), "flow"),
    (row("US", freq="M", year="202401"), "freq"),
    (row("US", reporter="IT"), "reporter"),
    (row("US", value="abc"), "non-numeric"),
    (row("US", value="-5"), "negative"),
    (row("CN", value="60"), "duplicated"),
])
def test_wrong_rows_are_refused(tmp_path, bad, message):
    with pytest.raises(DataError, match=message):
        load(write(tmp_path, balanced([bad])))


def test_unknown_product_is_refused(tmp_path):
    with pytest.raises(DataError, match="not in config"):
        load(write(tmp_path, [row("CN", product="999999")]))


def test_reconcile_spots_rows_that_do_not_add_up(tmp_path):
    lines = balanced()
    lines[0] = row("CN", value="65")      # countries now add up to 105, total says 100
    df = tidy(read_raw(write(tmp_path, lines)))
    bad = reconcile(df)
    assert len(bad) == 1
    with pytest.raises(DataError, match="do not add up"):
        load(write(tmp_path, lines, "again.csv"))


def test_full_data_file_passes_all_checks():
    data, audit = load(C.DATA_FILE)
    assert audit["reconciliation_mismatches"] == 0
    n_combos = data[["product", "indicator", "year"]].drop_duplicates().shape[0]
    assert audit["reconciliation_checked"] == n_combos
    assert isinstance(data, pd.DataFrame)
