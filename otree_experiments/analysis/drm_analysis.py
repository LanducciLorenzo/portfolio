"""
Analysis of the DRM experiment.

Inputs (from the oTree admin, "Data" page):
  1. Custom export of the app drm_test  -> one row per recognition trial
  2. (optional) "All apps - wide" export -> questionnaire scores and exclusion checks

    python analysis/drm_analysis.py trials.csv [all_apps_wide.csv]
    python analysis/drm_analysis.py --demo        (uses fake data from simulate_data.py)
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

pd.set_option('display.width', 160)
pd.set_option('display.max_columns', 20)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis' / 'output'
TYPES = ['studied', 'critical_lure', 'unstudied_word', 'control_lure']
MODALITY_ORDER = ['visual_words', 'auditory_words', 'pictures']


def participant_table(trials):
    trials = trials.assign(old=(trials['response'] == 'old').astype(float))
    t = trials.pivot_table(index=['participant', 'modality', 'list_set'], columns='item_type',
                           values='old', aggfunc='mean').reset_index()
    t.columns.name = None
    t = t.rename(columns={k: f'p_old_{k}' for k in TYPES})
    t['false_memory_corrected'] = t['p_old_critical_lure'] - t['p_old_control_lure']
    t['n_trials'] = trials.groupby('participant').size().reindex(t['participant']).values
    # mean confidence for false memories (critical lures answered "old")
    fm = trials[(trials['item_type'] == 'critical_lure') & (trials['response'] == 'old')]
    t = t.merge(fm.groupby('participant')['confidence'].mean().rename('confidence_false_memories'),
                on='participant', how='left')
    return t


def add_questionnaire(table, wide):
    cols = {c.split('.player.')[-1]: c for c in wide.columns if c.startswith('drm_questionnaire.1.player.')}
    keep = {'participant.code': 'participant'}
    for f in ['visual_minus_verbal', 'attention_passed', 'used_notes']:
        if f in cols:
            keep[cols[f]] = f
    w = wide[list(keep)].rename(columns=keep)
    return table.merge(w, on='participant', how='left')


def main(trials_path, wide_path=None):
    OUT.mkdir(parents=True, exist_ok=True)
    trials = pd.read_csv(trials_path)
    t = participant_table(trials)
    excluded = t[t['n_trials'] != 48]
    if wide_path:
        t = add_questionnaire(t, pd.read_csv(wide_path))
        bad = (t.get('attention_passed', 1) == 0) | (t.get('used_notes', 0) == 1)
        excluded = pd.concat([excluded, t[bad]])
    t_clean = t[~t['participant'].isin(excluded['participant'])]
    print(f'Participants: {len(t)}  excluded: {excluded["participant"].nunique()}  analysed: {len(t_clean)}')

    means = t_clean.groupby('modality')[[f'p_old_{k}' for k in TYPES] + ['false_memory_corrected']].mean()
    means = means.reindex([m for m in MODALITY_ORDER if m in means.index])
    print('\nProportion of "old" answers by modality:\n', means.round(3))

    # 1) Is there a DRM effect? critical lures vs control lures (paired, within participants)
    d = t_clean['p_old_critical_lure'] - t_clean['p_old_control_lure']
    res = stats.ttest_rel(t_clean['p_old_critical_lure'], t_clean['p_old_control_lure'])
    print(f'\nDRM effect: mean difference = {d.mean():.3f}, t({len(d) - 1}) = {res.statistic:.2f}, p = {res.pvalue:.4f}, '
          f'Cohen\'s dz = {d.mean() / d.std(ddof=1):.2f}')

    # 2) Does the corrected false memory differ by modality? (one-way ANOVA + Kruskal-Wallis as a check)
    groups = [g['false_memory_corrected'].values for _, g in t_clean.groupby('modality')]
    if len(groups) > 1:
        f = stats.f_oneway(*groups)
        k = stats.kruskal(*groups)
        print(f'Modality: ANOVA F = {f.statistic:.2f}, p = {f.pvalue:.4f} | Kruskal-Wallis H = {k.statistic:.2f}, p = {k.pvalue:.4f}')

    # 3) Cognitive style: correlation between visual-minus-verbal index and false memory
    if 'visual_minus_verbal' in t_clean:
        sub = t_clean.dropna(subset=['visual_minus_verbal'])
        r = stats.pearsonr(sub['visual_minus_verbal'], sub['false_memory_corrected'])
        print(f'Visual-verbal style vs false memory: r = {r.statistic:.2f}, p = {r.pvalue:.4f} (n = {len(sub)})')

    # figure
    ax = means[[f'p_old_{k}' for k in TYPES]].plot(kind='bar', figsize=(8, 4.5), rot=0)
    ax.set_ylabel('Proportion "old"')
    ax.set_xlabel('')
    ax.set_ylim(0, 1.15)
    ax.legend(['Studied words', 'Critical lures', 'Unrelated words', 'Control lures'], frameon=False,
              ncol=4, loc='upper center')
    ax.set_title('Recognition by item type and presentation modality')
    plt.tight_layout()
    plt.savefig(OUT / 'drm_recognition.png', dpi=150)
    t.to_csv(OUT / 'drm_participants.csv', index=False)
    print(f'\nSaved: {OUT / "drm_recognition.png"} and drm_participants.csv')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        demo = ROOT / 'analysis' / 'demo_data'
        main(demo / 'drm_trials.csv', demo / 'drm_wide.csv')
    elif len(sys.argv) > 1:
        main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        print(__doc__)
