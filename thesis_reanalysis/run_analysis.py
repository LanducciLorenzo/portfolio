"""
Reproducible reanalysis of the MSc thesis on false memories (multimodal DRM paradigm).

    python run_analysis.py data/my_thesis_data.csv        (.csv, .xlsx or .sav)
    python run_analysis.py --demo                         (fake data, to test the pipeline)

Output in output/: results.md (APA-style report), tables (.csv) and figures (.png).

Analyses
1. Replication: 3 (condition, within) x 2 (visual style group, between) mixed ANOVA for each measure,
   Greenhouse-Geisser correction, Bonferroni-corrected follow-up comparisons (as in the thesis).
2. Extension: signal detection on recognition. Sensitivity (d') and response criterion (c) computed
   against unrelated items and against critical lures. Tests the thesis' interpretation that high
   visualisers adopt a stricter criterion for pictures.
3. Extension: the Paivio visual score as a continuous variable (correlations), which avoids the
   information lost with a median split.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

import config
from src import data as dataio
from src.anova import group_comparisons, mixed_anova, pairwise_paired
from src.sdt import check_counts, dprime_c, rate

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output'


def fmt_p(p):
    return 'p < .001' if p < .001 else f'p = {p:.3f}'.replace('0.', '.')


def p_cell(p):
    return '< .001' if p < .001 else f'{p:.3f}'.replace('0.', '.')


def apa_effect(e):
    return (f'F({e.df1:.2f}, {e.df2:.2f}) = {e.f:.2f}, {fmt_p(e.p)}, partial η² = {e.partial_eta2:.3f}'
            if e.epsilon != 1 else
            f'F({e.df1:.0f}, {e.df2:.0f}) = {e.f:.2f}, {fmt_p(e.p)}, partial η² = {e.partial_eta2:.3f}')


def analyse_measure(df, measure, label, lines, tables):
    y, complete = dataio.matrix(df, measure)
    y, groups = y[complete], df['group'].to_numpy()[complete]
    res = mixed_anova(y, groups, correction='gg')
    names = [config.CONDITION_LABELS[c] for c in config.CONDITIONS]
    lines.append(f'### {label}\n')
    lines.append(f'n = {len(y)} (low = {int((groups == config.GROUP_LABELS[0]).sum())}, '
                 f'high = {int((groups == config.GROUP_LABELS[1]).sum())}); '
                 f'Greenhouse-Geisser ε = {res["epsilon_gg"]:.3f}\n')
    means = pd.DataFrame(y, columns=names).assign(group=groups).groupby('group').agg(['mean', 'sem'])
    for key, title in [('condition', 'Condition'), ('group', 'Visual style group'),
                       ('condition_x_group', 'Condition × group')]:
        lines.append(f'- **{title}:** {apa_effect(res[key])}')
    lines.append('')
    lines.append('| Condition | Mean (SE), all | Low visualisers | High visualisers |')
    lines.append('|---|---|---|---|')
    for i, nme in enumerate(names):
        col = y[:, i]
        lo, hi = means.loc[config.GROUP_LABELS[0], (nme, 'mean')], means.loc[config.GROUP_LABELS[1], (nme, 'mean')]
        lines.append(f'| {nme} | {col.mean():.3f} ({stats.sem(col):.3f}) | {lo:.3f} | {hi:.3f} |')
    lines.append('')
    if res['condition'].p < config.ALPHA:
        lines.append('Pairwise comparisons between conditions (Bonferroni):')
        for r in pairwise_paired(y, names):
            lines.append(f'- {r["a"]} vs {r["b"]}: Δ = {r["mean_diff"]:.3f}, t({r["df"]}) = {r["t"]:.2f}, '
                         f'p(Bonf.) {fmt_p(r["p_adj"])[2:]}, dz = {r["dz"]:.2f}')
        lines.append('')
    if res['condition_x_group'].p < config.ALPHA:
        lines.append('Interaction follow-up: high vs low visualisers within each condition (Bonferroni):')
        for r in group_comparisons(y, groups, names, config.GROUP_LABELS):
            lines.append(f'- {r["condition"]}: low = {r["mean_low"]:.3f}, high = {r["mean_high"]:.3f}, '
                         f't({r["df"]}) = {r["t"]:.2f}, p(Bonf.) {fmt_p(r["p_adj"])[2:]}, d = {r["d"]:.2f}')
        lines.append('')
    for key in ['condition', 'group', 'condition_x_group']:
        e = res[key]
        tables.append(dict(measure=measure, effect=e.name, F=e.f, df1=e.df1, df2=e.df2, p=e.p,
                           partial_eta2=e.partial_eta2, epsilon=e.epsilon))
    return y, groups


def bar_figure(df, measure, label, fname):
    names = [config.CONDITION_LABELS[c] for c in config.CONDITIONS]
    y, complete = dataio.matrix(df, measure)
    y, groups = y[complete], df['group'].to_numpy()[complete]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for i, g in enumerate(config.GROUP_LABELS):
        sel = y[groups == g]
        ax.bar(x + (i - 0.5) * 0.38, sel.mean(axis=0), 0.38, yerr=stats.sem(sel, axis=0), capsize=3,
               label=config.GROUP_NAMES[g], color=['#9aa5ad', '#4c5d73'][i])
    ax.set_xticks(x, names)
    ax.set_ylabel('Proportion')
    ax.set_title(label)
    ax.legend(frameon=False)
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    plt.savefig(OUT / fname, dpi=150)
    plt.close()


def sdt_section(df, lines, tables):
    lines.append('## 2. Extension: signal detection on recognition\n')
    lines.append(f'Rates corrected with the log-linear rule; items per condition assumed: '
                 f'{config.N_RECOG_OLD} old, {config.N_RECOG_LURE} critical lures, {config.N_RECOG_NEW} unrelated new '
                 f'(check these numbers in `config.py`).\n')
    ok = all(check_counts(df[f'{m}_{c}'], n) for c in config.CONDITIONS
             for m, n in [('recog_hit', config.N_RECOG_OLD), ('recog_lure', config.N_RECOG_LURE),
                          ('recog_fa', config.N_RECOG_NEW)])
    if not ok:
        lines.append('> ⚠️ Some proportions are not compatible with these numbers of items: '
                     'correct N_RECOG_* in config.py before interpreting d\' and c.\n')
    sdt = pd.DataFrame({'id': df.get('id', pd.Series(range(len(df)))), 'group': df['group']})
    for c in config.CONDITIONS:
        h = rate(df[f'recog_hit_{c}'], config.N_RECOG_OLD)
        f = rate(df[f'recog_fa_{c}'], config.N_RECOG_NEW)
        lure = rate(df[f'recog_lure_{c}'], config.N_RECOG_LURE)
        sdt[f'dprime_{c}'], sdt[f'c_{c}'] = dprime_c(h, f)
        sdt[f'dprimelure_{c}'], sdt[f'clure_{c}'] = dprime_c(h, lure)
    for measure, label in [('dprime', "Sensitivity d' (hits vs unrelated new items)"),
                           ('c', 'Criterion c (hits vs unrelated new items)'),
                           ('dprimelure', "Lure discrimination d'L (hits vs critical lures)"),
                           ('clure', 'Criterion for critical lures cL (higher = more conservative)')]:
        analyse_measure(sdt, measure, label, lines, tables)
    sdt.to_csv(OUT / 'sdt_by_participant.csv', index=False)
    return sdt


def continuous_section(df, sdt, lines):
    if config.PAIVIO_COLUMN not in df.columns:
        return
    lines.append('## 3. Extension: Paivio visual score as a continuous variable\n')
    lines.append('| Measure | Condition | Pearson r | p | Spearman ρ | p |')
    lines.append('|---|---|---|---|---|---|')
    score = pd.to_numeric(df[config.PAIVIO_COLUMN], errors='coerce')
    for measure, src in [('recog_lure', df), ('clure', sdt), ('recall_hit', df)]:
        for c in config.CONDITIONS:
            v = pd.to_numeric(src[f'{measure}_{c}'], errors='coerce')
            ok = score.notna() & v.notna()
            r = stats.pearsonr(score[ok], v[ok])
            rho = stats.spearmanr(score[ok], v[ok])
            lines.append(f'| {measure} | {config.CONDITION_LABELS[c]} | {r.statistic:.3f} | {p_cell(r.pvalue)} '
                         f'| {rho.statistic:.3f} | {p_cell(rho.pvalue)} |')
    lines.append('\nNo correction for multiple comparisons is applied in this exploratory table.\n')


def main(path, demo=False):
    OUT.mkdir(exist_ok=True)
    df = dataio.load(path)
    problems, warnings = dataio.check(df)
    if problems:
        print('Problems in the data:\n- ' + '\n- '.join(problems))
        sys.exit(1)
    df = dataio.assign_groups(df)
    lines = ['# Reanalysis of the MSc thesis: false memories in the multimodal DRM paradigm\n']
    if demo:
        lines.append('> **SIMULATED DATA** – these results only test the pipeline and have no scientific value.\n')
    for w in warnings:
        lines.append(f'> Note: {w}')
    lines.append(f'Participants: {len(df)}. Groups: {df["group_rule"].iloc[0]}.\n')
    lines.append('## 1. Replication: 3 (condition) × 2 (visual style) mixed ANOVAs\n')
    tables = []
    for measure, label in config.MEASURES.items():
        analyse_measure(df, measure, label, lines, tables)
        bar_figure(df, measure, label, f'fig_{measure}.png')
    sdt = sdt_section(df, lines, tables)
    for m, lab in [('clure', 'Criterion for critical lures (cL)'), ('dprime', "Sensitivity d'")]:
        bar_figure(sdt, m, lab, f'fig_{m}.png')
    continuous_section(df, sdt, lines)
    pd.DataFrame(tables).to_csv(OUT / 'anova_table.csv', index=False)
    (OUT / 'results.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'Done. Report: {OUT / "results.md"}')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        import simulate_thesis_data
        demo_path = ROOT / 'data' / 'simulated_thesis_data.csv'
        simulate_thesis_data.simulate().to_csv(demo_path, index=False)
        main(demo_path, demo=True)
    elif len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print(__doc__)
