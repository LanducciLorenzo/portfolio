"""
Mixed-design ANOVA (one between-subjects factor x one within-subjects factor) written with NumPy/SciPy,
using the multivariate (contrast) approach used by SPSS GLM Repeated Measures:
- Type III sums of squares, also with unequal group sizes
- Greenhouse-Geisser and Huynh-Feldt corrections for the within-subjects effects
A one-way repeated-measures ANOVA is the special case with a single group.
"""
from dataclasses import dataclass

import numpy as np
from scipy import stats


def orthonormal_contrasts(k):
    """(k-1) x k matrix of orthonormal contrasts (Helmert, normalised)."""
    c = np.zeros((k - 1, k))
    for i in range(1, k):
        c[i - 1, :i] = 1
        c[i - 1, i] = -i
        c[i - 1] /= np.linalg.norm(c[i - 1])
    return c


@dataclass
class Effect:
    name: str
    ss: float
    df1: float
    df2: float
    f: float
    p: float
    partial_eta2: float
    epsilon: float = 1.0      # correction applied to df1 and df2 (1 = none)


def _sphericity_epsilons(y, groups, contrasts):
    """Greenhouse-Geisser and Huynh-Feldt epsilon from the pooled within-group covariance matrix."""
    labels = np.unique(groups)
    n, k = y.shape
    resid = np.vstack([y[groups == g] - y[groups == g].mean(axis=0) for g in labels])
    s = resid.T @ resid / (n - len(labels))
    v = contrasts @ s @ contrasts.T
    p = k - 1
    gg = np.trace(v) ** 2 / (p * np.trace(v @ v))
    df_err = n - len(labels)
    hf = (df_err + 1) * p * gg - 2
    hf = hf / (p * (df_err - p * gg))
    return float(np.clip(gg, 1 / p, 1)), float(np.clip(hf, 1 / p, 1))


def mixed_anova(y, groups, correction='gg'):
    """
    y: array (n_subjects x k_conditions); groups: array of length n_subjects (use one value for a
    repeated-measures ANOVA without a between factor). correction: 'gg', 'hf' or None.
    Returns a dict of Effect objects plus the epsilons.
    """
    y = np.asarray(y, dtype=float)
    groups = np.asarray(groups)
    if np.isnan(y).any():
        raise ValueError('missing values: remove incomplete participants before the ANOVA')
    n, k = y.shape
    labels = np.unique(groups)
    j = len(labels)
    n_j = np.array([np.sum(groups == g) for g in labels])
    if (n_j < 2).any():
        raise ValueError('every group needs at least 2 participants')
    c = orthonormal_contrasts(k)

    # ---- between subjects: subject means
    a = y.mean(axis=1)
    a_means = np.array([a[groups == g].mean() for g in labels])
    ss_subj_err = k * sum(((a[groups == g] - a[groups == g].mean()) ** 2).sum() for g in labels)
    df_subj_err = n - j
    out = {}
    if j > 1:
        ss_group = k * np.sum(n_j * (a_means - a.mean()) ** 2)
        f = (ss_group / (j - 1)) / (ss_subj_err / df_subj_err)
        out['group'] = Effect('group', ss_group, j - 1, df_subj_err, f, stats.f.sf(f, j - 1, df_subj_err),
                              ss_group / (ss_group + ss_subj_err))

    # ---- within subjects: transformed (contrast) scores
    z = y @ c.T                                   # n x (k-1)
    zbar_j = np.array([z[groups == g].mean(axis=0) for g in labels])   # j x (k-1)
    # Type III intercept on each contrast = condition effect (evaluated at the unweighted mean of groups)
    est = zbar_j.mean(axis=0)
    ss_cond = float(np.sum(est ** 2) / (np.sum(1 / n_j) / j ** 2))
    ss_err = float(sum(((z[groups == g] - z[groups == g].mean(axis=0)) ** 2).sum() for g in labels))
    df_cond, df_err = k - 1, (n - j) * (k - 1)
    gg, hf = _sphericity_epsilons(y, groups, c) if k > 2 else (1.0, 1.0)
    eps = {'gg': gg, 'hf': hf, None: 1.0}[correction]

    def within(name, ss, df):
        f = (ss / df) / (ss_err / df_err)
        p = stats.f.sf(f, df * eps, df_err * eps)
        return Effect(name, ss, df * eps, df_err * eps, f, p, ss / (ss + ss_err), eps)

    out['condition'] = within('condition', ss_cond, df_cond)
    if j > 1:
        ss_inter = float(np.sum(n_j[:, None] * (zbar_j - z.mean(axis=0)) ** 2))
        out['condition_x_group'] = within('condition x group', ss_inter, (k - 1) * (j - 1))
    out['epsilon_gg'] = gg
    out['epsilon_hf'] = hf
    out['ss_error_within'] = ss_err
    out['ss_error_between'] = ss_subj_err
    return out


def pairwise_paired(y, names, adjust='bonferroni'):
    """Paired t-tests between all pairs of conditions, Bonferroni-corrected."""
    y = np.asarray(y, dtype=float)
    pairs = [(a, b) for a in range(len(names)) for b in range(a + 1, len(names))]
    rows = []
    for a, b in pairs:
        t = stats.ttest_rel(y[:, a], y[:, b])
        d = y[:, a] - y[:, b]
        p_adj = min(1.0, t.pvalue * len(pairs)) if adjust == 'bonferroni' else t.pvalue
        rows.append(dict(a=names[a], b=names[b], mean_diff=d.mean(), t=t.statistic, df=len(d) - 1,
                         p=t.pvalue, p_adj=p_adj, dz=d.mean() / d.std(ddof=1)))
    return rows


def group_comparisons(y, groups, names, labels, adjust='bonferroni'):
    """Independent-samples t-tests between the two groups within each condition (Bonferroni)."""
    y = np.asarray(y, dtype=float)
    rows = []
    g0, g1 = labels
    for c, name in enumerate(names):
        x0, x1 = y[groups == g0, c], y[groups == g1, c]
        t = stats.ttest_ind(x1, x0)
        sp = np.sqrt(((len(x0) - 1) * x0.var(ddof=1) + (len(x1) - 1) * x1.var(ddof=1)) / (len(x0) + len(x1) - 2))
        rows.append(dict(condition=name, mean_low=x0.mean(), mean_high=x1.mean(), t=t.statistic,
                         df=len(x0) + len(x1) - 2, p=t.pvalue,
                         p_adj=min(1.0, t.pvalue * len(names)) if adjust == 'bonferroni' else t.pvalue,
                         d=(x1.mean() - x0.mean()) / sp))
    return rows
