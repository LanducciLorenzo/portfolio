"""
Settings for the reanalysis of the MSc thesis
"False memories in the multimodal DRM paradigm: presentation modality and visual-verbal cognitive style".
Change these values to match the real dataset.
"""

# Conditions (within subjects) and their labels in the figures
CONDITIONS = ['immagini', 'concrete', 'astratte']
CONDITION_LABELS = {'immagini': 'Pictures', 'concrete': 'Concrete words', 'astratte': 'Abstract words'}

# Dependent variables: column names in the data are  <test>_<measure>_<condition>,
# e.g. recog_lure_immagini = proportion of critical lures recognised as "old" in the picture condition.
MEASURES = {
    'recall_hit':  'Correct recall (proportion of list items)',
    'recall_lure': 'Critical lure recall (false recall)',
    'recog_hit':   'Correct recognition (hits)',
    'recog_lure':  'Critical lure recognition (false recognition)',
    'recog_fa':    'False alarms to unrelated items',
}

# Grouping by cognitive style (between subjects).
# If the data have a column GROUP_COLUMN (values in GROUP_LABELS) it is used as it is;
# otherwise participants are split at the median of PAIVIO_COLUMN.
GROUP_COLUMN = 'gruppo'
PAIVIO_COLUMN = 'paivio_visivo'
GROUP_LABELS = ['basso', 'alto']          # low visualisers, high visualisers
GROUP_NAMES = {'basso': 'Low visualisers', 'alto': 'High visualisers'}

# Number of items per condition in the recognition test, used for signal detection.
# CHECK against the real materials: the thesis reports 30 items per block (15 old);
# 5 critical lures (one per list) and 10 unrelated items are assumed here.
N_RECOG_OLD = 15
N_RECOG_LURE = 5
N_RECOG_NEW = 10

ALPHA = 0.05
