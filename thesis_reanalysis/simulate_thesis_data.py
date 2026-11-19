"""
Creates a FAKE dataset with the same structure as the thesis dataset, with means close to those
reported in the thesis, only to test the pipeline. Never use it for conclusions.
    python simulate_thesis_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

import config

rng = np.random.default_rng(2026)
N = 130
# condition means (immagini, concrete, astratte) approximately as reported in the thesis
MEANS = {
    'recall_hit':  [0.717, 0.599, 0.489],
    'recall_lure': [0.108, 0.194, 0.233],
    'recog_hit':   [0.898, 0.763, 0.772],
    'recog_lure':  [0.317, 0.650, 0.677],
    'recog_fa':    [0.040, 0.022, 0.105],
}
N_ITEMS = {'recall_hit': 75, 'recall_lure': 5, 'recog_hit': config.N_RECOG_OLD,
           'recog_lure': config.N_RECOG_LURE, 'recog_fa': config.N_RECOG_NEW}


def simulate():
    paivio = rng.normal(50, 10, N).round(1)
    visual = (paivio - paivio.mean()) / paivio.std()
    rows = {'id': np.arange(1, N + 1), config.PAIVIO_COLUMN: paivio}
    person = rng.normal(0, 1, N)                       # general memory ability
    for m, means in MEANS.items():
        for c, mu in zip(config.CONDITIONS, means):
            logit = np.log(mu / (1 - mu)) + 0.35 * person + rng.normal(0, 0.45, N)
            if m == 'recall_hit':
                logit += 0.08 * visual                 # small advantage of visualisers in recall
            if m == 'recog_lure' and c == 'immagini':
                logit -= 0.20 * visual                 # visualisers: fewer false recognitions of pictures
            p = 1 / (1 + np.exp(-logit))
            n = N_ITEMS[m]
            rows[f'{m}_{c}'] = rng.binomial(n, p) / n
    return pd.DataFrame(rows)


if __name__ == '__main__':
    out = Path(__file__).parent / 'data' / 'simulated_thesis_data.csv'
    simulate().to_csv(out, index=False)
    print('fake data written to', out)
