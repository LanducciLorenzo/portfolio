"""
Three levels of checks on the statistics (run: python tests/test_stats.py)
1. Independent recomputation: the mixed ANOVA is compared with a regression (least squares) model
   and with textbook formulas.
2. Known values: signal detection and sphericity on cases with a known answer.
3. Simulation: the tests find effects that exist and keep the false positive rate near 5%.
"""
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.anova import mixed_anova, orthonormal_contrasts  # noqa: E402
from src.sdt import check_counts, dprime_c, rate  # noqa: E402

rng = np.random.default_rng(7)


def ols_rss(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ beta
    return float(r @ r)


def regression_type3(y, groups):
    """Within-subject effects with Type III SS from a regression: y ~ subject + condition + condition:group,
    effect (sum-to-zero) coding. Independent from the contrast method used in src/anova.py."""
    n, k = y.shape
    labels = np.unique(groups)
    yy = y.reshape(-1)
    subj = np.repeat(np.arange(n), k)
    cond = np.tile(np.arange(k), n)
    S = np.eye(n)[subj]                                         # subject dummies (absorb group)
    Cc = np.zeros((n * k, k - 1))
    for c in range(k - 1):
        Cc[:, c] = (cond == c).astype(float) - (cond == k - 1)
    g = np.array([np.where(labels == x)[0][0] for x in groups])[subj]
    G = np.zeros((n * k, len(labels) - 1))
    for j in range(len(labels) - 1):
        G[:, j] = (g == j).astype(float) - (g == len(labels) - 1)
    CG = np.hstack([Cc[:, [a]] * G[:, [b]] for a in range(k - 1) for b in range(len(labels) - 1)])
    full = np.hstack([S, Cc, CG])
    rss_full = ols_rss(full, yy)
    ss_cond = ols_rss(np.hstack([S, CG]), yy) - rss_full
    ss_inter = ols_rss(np.hstack([S, Cc]), yy) - rss_full
    return ss_cond, ss_inter, rss_full


# ---------------------------------------------------------------- level 1
def test_against_regression_unbalanced():
    for n0, n1, k in [(20, 20, 3), (17, 29, 3), (9, 14, 4), (30, 11, 2)]:
        y = rng.normal(size=(n0 + n1, k)) + rng.normal(size=(n0 + n1, 1))
        y[:n0] += np.linspace(0, 0.5, k)
        groups = np.array(['a'] * n0 + ['b'] * n1)
        res = mixed_anova(y, groups, correction=None)
        ss_cond, ss_inter, ss_err = regression_type3(y, groups)
        assert np.isclose(res['condition'].ss, ss_cond), (n0, n1, k, res['condition'].ss, ss_cond)
        assert np.isclose(res['condition_x_group'].ss, ss_inter)
        assert np.isclose(res['ss_error_within'], ss_err)


def test_textbook_balanced_and_total():
    n, k = 24, 3
    y = rng.normal(size=(n, k)) + np.array([0, .3, .6])
    groups = np.array(['a', 'b'] * (n // 2))
    res = mixed_anova(y, groups, correction=None)
    M = y.mean()
    ss_total = ((y - M) ** 2).sum()
    parts = (res['group'].ss + res['ss_error_between'] + res['condition'].ss
             + res['condition_x_group'].ss + res['ss_error_within'])
    assert np.isclose(ss_total, parts)                       # the sums of squares add up
    assert np.isclose(res['condition'].ss, n * ((y.mean(axis=0) - M) ** 2).sum())   # balanced: textbook formula


def test_one_way_repeated_measures():
    n, k = 15, 3
    y = rng.normal(size=(n, k)) + np.array([0, .4, .8])
    res = mixed_anova(y, np.zeros(n), correction=None)
    M = y.mean()
    ss_c = n * ((y.mean(axis=0) - M) ** 2).sum()
    ss_s = k * ((y.mean(axis=1) - M) ** 2).sum()
    ss_e = ((y - M) ** 2).sum() - ss_c - ss_s
    f = (ss_c / (k - 1)) / (ss_e / ((n - 1) * (k - 1)))
    assert np.isclose(res['condition'].f, f)
    assert 'group' not in res


def test_two_levels_equals_t_test():
    # with 2 conditions and 1 group, F = t^2 of the paired t-test
    y = rng.normal(size=(30, 2)) + [0, .3]
    res = mixed_anova(y, np.zeros(30), correction='gg')
    t = stats.ttest_rel(y[:, 0], y[:, 1])
    assert np.isclose(res['condition'].f, t.statistic ** 2) and np.isclose(res['condition'].p, t.pvalue)


def test_group_effect_equals_t_test_on_means():
    # the between-subjects effect = independent t-test on each participant's mean
    y = rng.normal(size=(40, 3))
    groups = np.array(['a'] * 18 + ['b'] * 22)
    y[groups == 'b'] += .5
    res = mixed_anova(y, groups)
    m = y.mean(axis=1)
    t = stats.ttest_ind(m[groups == 'a'], m[groups == 'b'])
    assert np.isclose(res['group'].f, t.statistic ** 2) and np.isclose(res['group'].p, t.pvalue)


# ---------------------------------------------------------------- level 2
def test_contrasts_orthonormal():
    for k in [2, 3, 5]:
        c = orthonormal_contrasts(k)
        assert np.allclose(c @ c.T, np.eye(k - 1)) and np.allclose(c.sum(axis=1), 0)


def test_epsilon_sphericity():
    # compound symmetry (sphericity true) -> epsilon close to 1; strong violation -> much lower
    n, k = 4000, 3
    cov = np.full((k, k), .5) + np.eye(k) * .5
    y = rng.multivariate_normal(np.zeros(k), cov, n)
    assert mixed_anova(y, np.zeros(n))['epsilon_gg'] > .99
    cov2 = np.array([[1, .9, .1], [.9, 1, .1], [.1, .1, 1]])
    y2 = rng.multivariate_normal(np.zeros(k), cov2, n)
    e = mixed_anova(y2, np.zeros(n))['epsilon_gg']
    assert .5 <= e < .8, e


def test_sdt_known_values():
    d, c = dprime_c(0.84134, 0.15866)          # z = +1 and -1
    assert np.isclose(d, 2, atol=1e-3) and np.isclose(c, 0, atol=1e-3)
    d, c = dprime_c(0.5, 0.15866)              # conservative observer
    assert np.isclose(d, 1, atol=1e-3) and np.isclose(c, 0.5, atol=1e-3)
    assert np.isclose(rate(1.0, 15), 15.5 / 16) and np.isclose(rate(0.0, 10), 0.5 / 11)
    assert check_counts([0, 0.2, 0.4, 1], 5) and not check_counts([0.33], 5)


# ---------------------------------------------------------------- level 3
def test_recovers_real_effects():
    y = rng.normal(size=(60, 3)) * .15 + [.7, .6, .5]
    groups = np.array(['a', 'b'] * 30)
    y[groups == 'b', 0] -= .12                  # interaction: group b lower only in condition 1
    res = mixed_anova(y, groups)
    assert res['condition'].p < .001 and res['condition_x_group'].p < .05


def test_false_positive_rate():
    hits = 0
    reps = 400
    for _ in range(reps):
        y = rng.normal(size=(40, 3)) + rng.normal(size=(40, 1))
        res = mixed_anova(y, np.array(['a'] * 20 + ['b'] * 20))
        hits += res['condition_x_group'].p < .05
    rate_ = hits / reps
    assert .02 <= rate_ <= .09, rate_


if __name__ == '__main__':
    tests = [v for k, v in dict(globals()).items() if k.startswith('test_')]
    for t in tests:
        t()
        print('OK ', t.__name__)
    print(f'{len(tests)} tests passed')
