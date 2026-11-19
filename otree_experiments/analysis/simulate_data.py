"""
Creates FAKE data in the same format as the oTree exports, only to test the analysis scripts
before real data exist. Never use these data for conclusions.
    python analysis/simulate_data.py
"""
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from drm_common.logic import assign_conditions, build_test_items

OUT = ROOT / 'analysis' / 'demo_data'
OUT.mkdir(parents=True, exist_ok=True)
rng = random.Random(42)
np_rng = np.random.default_rng(42)

# ---------- DRM: 60 fake participants ----------
P_OLD = {  # assumed probabilities of answering "old" (made up for the demo)
    'visual_words':   dict(studied=.75, critical_lure=.60, unstudied_word=.12, control_lure=.15),
    'auditory_words': dict(studied=.70, critical_lure=.70, unstudied_word=.12, control_lure=.15),
    'pictures':       dict(studied=.85, critical_lure=.35, unstudied_word=.08, control_lure=.10),
}
trial_rows, wide_rows = [], []
for i in range(1, 61):
    cond = assign_conditions(i, 'random', rng)
    code = f'demo{i:03d}'
    style = np_rng.normal(0, 1)   # visual - verbal index
    for it in build_test_items(cond['studied_lists'], rng):
        p = P_OLD[cond['modality']][it['item_type']]
        if it['item_type'] == 'critical_lure':
            p = min(.95, max(.05, p - 0.05 * style))   # fake: more visual -> fewer false memories
        resp = 'old' if rng.random() < p else 'new'
        trial_rows.append(['DEMO', code, cond['modality'], cond['list_set'], it['order'], it['item'],
                           it['item_type'], it['list_id'], resp, rng.randint(1, 4), int(np_rng.normal(1100, 250))])
    wide_rows.append({'participant.code': code,
                      'drm_questionnaire.1.player.visual_minus_verbal': round(style, 2),
                      'drm_questionnaire.1.player.attention_passed': int(rng.random() > .05),
                      'drm_questionnaire.1.player.used_notes': int(rng.random() < .05)})
pd.DataFrame(trial_rows, columns=['session', 'participant', 'modality', 'list_set', 'order', 'item', 'item_type',
                                  'list_id', 'response', 'confidence', 'rt_ms']).to_csv(OUT / 'drm_trials.csv', index=False)
pd.DataFrame(wide_rows).to_csv(OUT / 'drm_wide.csv', index=False)

# ---------- PGG: 2 sessions per condition ----------
rows = []
for treatment in ['equal', 'unequal']:
    for matching in ['partner', 'stranger']:
        for s in range(2):
            n = 8
            endow = [20] * 4 if treatment == 'equal' else [10, 10, 30, 30]
            for pid in range(n):
                e = endow[pid % 4]
                base = .55 if treatment == 'equal' else .45
                if treatment == 'unequal' and e == 30:
                    base -= .1
                for r in range(1, 11):
                    decay = .03 * r if matching == 'stranger' else .015 * r
                    share = float(np.clip(np_rng.normal(base - decay, .2), 0, 1))
                    c = int(round(share * e))
                    rows.append({'session.code': f'{treatment}_{matching}_{s}', 'participant.code': f'{treatment}{matching}{s}_{pid}',
                                 'subsession.round_number': r, 'group.id_in_subsession': pid // 4 + 1,
                                 'player.treatment': treatment, 'player.matching': matching, 'player.endowment': e,
                                 'player.is_high_endowment': int(treatment == 'unequal' and e == 30),
                                 'player.contribution': c, 'player.contribution_share': c / e,
                                 'player.timed_out': 0})
pd.DataFrame(rows).to_csv(OUT / 'pgg.csv', index=False)
print('fake data written to', OUT)
