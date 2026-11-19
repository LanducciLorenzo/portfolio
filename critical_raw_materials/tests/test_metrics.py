"""Tests for the HHI and the scenario arithmetic, against values worked out by hand."""
import numpy as np
import pandas as pd
import pytest

from src.metrics import equivalent_suppliers, hhi
from src.scenario import (hhi_after_shift_closed_form, shift, shift_for_hhi,
                          shift_for_max_share)


def s(**kw):
    return pd.Series(kw, dtype=float)


def test_hhi_monopoly_is_10000():
    assert hhi(s(CN=1.0)) == pytest.approx(10_000)


@pytest.mark.parametrize("n", [2, 4, 5, 10])
def test_hhi_equal_suppliers(n):
    share = pd.Series([1 / n] * n, index=[f"C{i}" for i in range(n)])
    assert hhi(share) == pytest.approx(10_000 / n)
    assert equivalent_suppliers(hhi(share)) == pytest.approx(n)


def test_hhi_textbook_example():
    # 50%, 30%, 20%  ->  2500 + 900 + 400
    assert hhi(s(A=0.5, B=0.3, C=0.2)) == pytest.approx(3800)


def test_hhi_rejects_shares_not_summing_to_one():
    with pytest.raises(ValueError):
        hhi(s(A=0.5, B=0.3))


def test_shift_zero_changes_nothing():
    share = s(CN=0.6, CL=0.3, AU=0.1)
    out = shift(share, 0.0)
    assert out.to_dict() == pytest.approx(share.to_dict())


def test_shift_moves_exact_amount_and_keeps_total():
    out = shift(s(CN=0.6, CL=0.3, AU=0.1), 0.25)
    assert out["CN"] == pytest.approx(0.45)
    assert out["AU"] == pytest.approx(0.25)
    assert out["CL"] == pytest.approx(0.3)
    assert out.sum() == pytest.approx(1.0)


def test_shift_adds_australia_if_absent_and_full_shift_removes_china():
    out = shift(s(CN=0.7, CL=0.3), 1.0)
    assert "CN" not in out.index
    assert out["AU"] == pytest.approx(0.7)


def test_shift_rejects_bad_fraction():
    with pytest.raises(ValueError):
        shift(s(CN=1.0), 1.5)


def test_shift_matches_closed_form_on_random_markets():
    rng = np.random.default_rng(42)
    for _ in range(300):
        n = rng.integers(2, 12)
        w = rng.dirichlet(np.ones(n))
        codes = ["CN", "AU"] + [f"X{i}" for i in range(n - 2)]
        share = pd.Series(w, index=codes)
        frac = rng.uniform(0, 1)
        expected = hhi_after_shift_closed_form(hhi(share), share["CN"], share["AU"], frac)
        assert hhi(shift(share, frac)) == pytest.approx(expected, rel=1e-9)


def test_shift_for_max_share():
    share = s(CN=0.9, AU=0.0, US=0.1)
    needed = shift_for_max_share(share, 0.65)
    assert needed == pytest.approx(1 - 0.65 / 0.9)
    assert shift(share, needed)["CN"] == pytest.approx(0.65)
    assert shift_for_max_share(s(CN=0.4, CL=0.6), 0.65) == 0.0


def test_shift_for_hhi_finds_the_smallest_fraction():
    share = s(CN=0.8, US=0.1, JP=0.1)
    target = 4000
    needed = shift_for_hhi(share, target)
    assert needed is not None
    assert hhi(shift(share, needed)) <= target + 1e-6
    assert hhi(shift(share, max(needed - 1e-3, 0))) > target


def test_shift_for_hhi_unreachable_returns_none():
    # Chile dominates: moving China's small share to Australia cannot fix it
    assert shift_for_hhi(s(CL=0.9, CN=0.1), 1800) is None
    # Already below target
    assert shift_for_hhi(s(A=0.25, B=0.25, C=0.25, D=0.25), 3000) == 0.0
