"""
Analysis of the public goods game.

Input: the app export of pgg_inequality from the oTree admin ("Data" page -> pgg_inequality).
    python analysis/pgg_analysis.py pgg_inequality.csv
    python analysis/pgg_analysis.py --demo

Note on statistics: decisions of players in the same group are not independent. With fixed groups
the independent unit is the group; with new groups every round it is the whole session (matching group).
This script therefore tests on group/session averages, not on individual decisions.
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


def main(path):
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(path)
    df = df.rename(columns=lambda c: c.replace('player.', '').replace('subsession.', '').replace('group.', 'group_'))
    df = df.dropna(subset=['contribution'])
    print(f'Decisions: {len(df)}  participants: {df["participant.code"].nunique()}  '
          f'timeouts: {int(df.get("timed_out", pd.Series(0)).sum())}')

    # independent unit: group (partner) or session (stranger)
    df['unit'] = df['session.code'].astype(str)
    partner = df['matching'] == 'partner'
    df.loc[partner, 'unit'] = df.loc[partner, 'session.code'].astype(str) + '_g' + df.loc[partner, 'group_id_in_subsession'].astype(str)
    units = df.groupby(['unit', 'treatment', 'matching'])['contribution_share'].mean().reset_index()

    table = units.groupby(['treatment', 'matching'])['contribution_share'].agg(['mean', 'std', 'count'])
    print('\nMean share of endowment contributed (unit = group or session):\n', table.round(3))

    for matching, g in units.groupby('matching'):
        eq = g.loc[g['treatment'] == 'equal', 'contribution_share']
        un = g.loc[g['treatment'] == 'unequal', 'contribution_share']
        if len(eq) > 1 and len(un) > 1:
            u = stats.mannwhitneyu(eq, un, alternative='two-sided')
            print(f'{matching}: equal {eq.mean():.3f} vs unequal {un.mean():.3f}, Mann-Whitney U = {u.statistic:.1f}, p = {u.pvalue:.4f}')

    # rich vs poor in the unequal treatment (within the same units)
    une = df[df['treatment'] == 'unequal']
    if len(une):
        rp = une.groupby(['unit', 'is_high_endowment'])['contribution_share'].mean().unstack()
        rp = rp.dropna()
        if len(rp) > 1:
            w = stats.wilcoxon(rp[1], rp[0])
            print(f'Unequal: high-endowment share {rp[1].mean():.3f} vs low {rp[0].mean():.3f}, '
                  f'Wilcoxon p = {w.pvalue:.4f} (n units = {len(rp)})')

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for (treatment, matching), g in df.groupby(['treatment', 'matching']):
        g.groupby('round_number')['contribution_share'].mean().plot(
            ax=ax, marker='o', linestyle='-' if treatment == 'equal' else '--', label=f'{treatment}, {matching}')
    ax.set_xlabel('Round')
    ax.set_ylabel('Share of endowment contributed')
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    ax.set_title('Cooperation over rounds')
    plt.tight_layout()
    plt.savefig(OUT / 'pgg_rounds.png', dpi=150)
    print(f'\nSaved: {OUT / "pgg_rounds.png"}')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        main(ROOT / 'analysis' / 'demo_data' / 'pgg.csv')
    elif len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print(__doc__)
