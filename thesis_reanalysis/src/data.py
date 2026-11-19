"""Loading and checking the thesis dataset (one row per participant)."""
from pathlib import Path

import numpy as np
import pandas as pd

import config


def load(path):
    path = Path(path)
    if path.suffix.lower() == '.sav':
        try:
            df = pd.read_spss(path)        # needs: pip install pyreadstat
        except ImportError as e:
            raise ImportError('To read SPSS files run: pip install pyreadstat') from e
    elif path.suffix.lower() in ('.xlsx', '.xls'):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def required_columns():
    return [f'{m}_{c}' for m in config.MEASURES for c in config.CONDITIONS]


def check(df):
    """Return (problems, warnings) about the dataset."""
    problems, warnings = [], []
    missing = [c for c in required_columns() if c not in df.columns]
    if missing:
        problems.append(f'missing columns: {missing}')
    if config.GROUP_COLUMN not in df.columns and config.PAIVIO_COLUMN not in df.columns:
        problems.append(f'need either a "{config.GROUP_COLUMN}" or a "{config.PAIVIO_COLUMN}" column')
    for c in required_columns():
        if c in df.columns:
            vals = pd.to_numeric(df[c], errors='coerce')
            if vals.isna().any():
                warnings.append(f'{c}: {int(vals.isna().sum())} missing or non-numeric values')
            if ((vals < 0) | (vals > 1)).any():
                problems.append(f'{c}: values outside 0-1 (proportions expected; if these are counts, divide by N items)')
    if 'id' in df.columns and df['id'].duplicated().any():
        problems.append('duplicated participant ids')
    return problems, warnings


def assign_groups(df):
    """Group column if present, else median split of the Paivio visual score (median -> low group)."""
    df = df.copy()
    if config.GROUP_COLUMN in df.columns:
        df['group'] = df[config.GROUP_COLUMN].astype(str).str.strip().str.lower()
        unknown = set(df['group']) - set(config.GROUP_LABELS)
        if unknown:
            raise ValueError(f'unknown group labels {unknown}; expected {config.GROUP_LABELS}')
        df['group_rule'] = 'given'
    else:
        score = pd.to_numeric(df[config.PAIVIO_COLUMN], errors='coerce')
        med = score.median()
        df['group'] = np.where(score > med, config.GROUP_LABELS[1], config.GROUP_LABELS[0])
        df['group_rule'] = f'median split at {med:g}'
    return df


def matrix(df, measure):
    """n x k array for one measure, in the order of config.CONDITIONS, and the complete-case mask."""
    cols = [f'{measure}_{c}' for c in config.CONDITIONS]
    m = df[cols].apply(pd.to_numeric, errors='coerce').to_numpy()
    complete = ~np.isnan(m).any(axis=1)
    return m, complete
