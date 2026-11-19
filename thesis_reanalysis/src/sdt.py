"""Signal detection measures for recognition data."""
import numpy as np
from scipy.stats import norm


def rate(proportion, n_items, correction=True):
    """Proportion -> rate. With correction, the log-linear rule (Hautus, 1995): (count + 0.5) / (n + 1),
    which avoids infinite z-scores when a rate is 0 or 1."""
    p = np.asarray(proportion, dtype=float)
    if not correction:
        return p
    count = np.round(p * n_items)
    return (count + 0.5) / (n_items + 1)


def dprime_c(hit_rate, fa_rate):
    """Sensitivity d' = z(H) - z(F) and response criterion c = -(z(H) + z(F)) / 2.
    Positive c = conservative criterion (tendency to answer 'new')."""
    zh, zf = norm.ppf(hit_rate), norm.ppf(fa_rate)
    return zh - zf, -(zh + zf) / 2


def check_counts(proportion, n_items, tol=0.02):
    """True if proportion x n_items is (close to) a whole number of items, i.e. N items is plausible."""
    p = np.asarray(proportion, dtype=float)
    p = p[~np.isnan(p)]
    return bool(np.all(np.abs(p * n_items - np.round(p * n_items)) < tol * n_items + 1e-9))
