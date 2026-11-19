"""What-if scenario: part of China's supply is replaced by Australian supply.

This is arithmetic, not a forecast. It asks: if a share s of what the EU now
imports from China came from Australia instead (total imports unchanged), how
would concentration change? It does not model prices, capacity, or whether
Australia could actually supply that amount.
"""
from __future__ import annotations

import pandas as pd

from src.metrics import hhi


def shift(share: pd.Series, s: float, source: str = "CN", dest: str = "AU") -> pd.Series:
    """Move a fraction s of the source country's share to the destination country."""
    if not 0 <= s <= 1:
        raise ValueError("s must be between 0 and 1")
    out = share.copy()
    if dest not in out.index:
        out[dest] = 0.0
    moved = out.get(source, 0.0) * s
    if source in out.index:
        out[source] -= moved
    out[dest] += moved
    return out[out > 1e-15].sort_values(ascending=False)


def hhi_after_shift_closed_form(h0: float, c: float, a: float, s: float) -> float:
    """Same result as hhi(shift(...)) using algebra, used to test the code.

    Only the two countries involved change:
    new HHI = old HHI - (c^2 + a^2) + (c(1-s))^2 + (a + cs)^2, in percent points.
    """
    c100, a100 = 100 * c, 100 * a
    return h0 - c100 ** 2 - a100 ** 2 + (c100 * (1 - s)) ** 2 + (a100 + c100 * s) ** 2


def shift_for_max_share(share: pd.Series, limit: float, source: str = "CN") -> float | None:
    """Smallest s that brings the source country's share down to the limit.

    Returns 0 if it is already at or below the limit.
    """
    c = float(share.get(source, 0.0))
    if c <= limit:
        return 0.0
    return 1 - limit / c


def shift_for_hhi(share: pd.Series, target: float, source: str = "CN", dest: str = "AU",
                  tol: float = 1e-6) -> float | None:
    """Smallest s that brings the HHI down to the target, or None if no s can.

    HHI(s) is a parabola in s with its minimum where the two countries have
    equal shares, so we search only between 0 and that point.
    """
    if hhi(share) <= target:
        return 0.0
    c = float(share.get(source, 0.0))
    a = float(share.get(dest, 0.0))
    if c <= a:
        return None
    s_min = (c - a) / (2 * c)
    if hhi(shift(share, s_min, source, dest)) > target:
        return None
    lo, hi = 0.0, s_min
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if hhi(shift(share, mid, source, dest)) > target:
            lo = mid
        else:
            hi = mid
    return hi
