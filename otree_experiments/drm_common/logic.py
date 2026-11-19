"""
Pure-Python logic for the DRM experiment (no oTree imports), so it can be tested on its own.

Materials: 12 DRM lists based on Roediger & McDermott (1995), first 12 associates of each
critical lure in order of backward associative strength. CHECK them against the published
norms (Stadler, Roediger & McDermott, 1999) before running a real study.
"""
import random

# critical lure -> 12 associates (presentation order = associative strength, strongest first)
DRM_LISTS = {
    'sleep':    ['bed', 'rest', 'awake', 'tired', 'dream', 'wake', 'snooze', 'blanket', 'doze', 'slumber', 'snore', 'nap'],
    'chair':    ['table', 'sit', 'legs', 'seat', 'couch', 'desk', 'recliner', 'sofa', 'wood', 'cushion', 'swivel', 'stool'],
    'mountain': ['hill', 'valley', 'climb', 'summit', 'top', 'molehill', 'peak', 'plain', 'glacier', 'goat', 'bike', 'climber'],
    'needle':   ['thread', 'pin', 'eye', 'sewing', 'sharp', 'point', 'prick', 'thimble', 'haystack', 'thorn', 'hurt', 'injection'],
    'sweet':    ['sour', 'candy', 'sugar', 'bitter', 'good', 'taste', 'tooth', 'nice', 'honey', 'soda', 'chocolate', 'heart'],
    'doctor':   ['nurse', 'sick', 'lawyer', 'medicine', 'health', 'hospital', 'dentist', 'physician', 'ill', 'patient', 'office', 'stethoscope'],
    'cold':     ['hot', 'snow', 'warm', 'winter', 'ice', 'wet', 'frigid', 'chilly', 'heat', 'weather', 'freeze', 'air'],
    'window':   ['door', 'glass', 'pane', 'shade', 'ledge', 'sill', 'house', 'open', 'curtain', 'frame', 'view', 'breeze'],
    'soft':     ['hard', 'light', 'pillow', 'plush', 'loud', 'cotton', 'fur', 'touch', 'fluffy', 'feather', 'furry', 'downy'],
    'smell':    ['nose', 'breathe', 'sniff', 'aroma', 'hear', 'see', 'nostril', 'whiff', 'scent', 'reek', 'stench', 'fragrance'],
    'river':    ['water', 'stream', 'lake', 'boat', 'tide', 'swim', 'flow', 'run', 'barge', 'creek', 'brook', 'fish'],
    'music':    ['note', 'sound', 'piano', 'sing', 'radio', 'band', 'melody', 'horn', 'concert', 'instrument', 'symphony', 'jazz'],
}

# Counterbalancing: half of the participants study set A, the other half set B.
# Lists that are not studied provide the control lures in the recognition test.
LIST_SETS = {
    'A': ['sleep', 'chair', 'mountain', 'needle', 'sweet', 'doctor'],
    'B': ['cold', 'window', 'soft', 'smell', 'river', 'music'],
}

# Positions (0-based) of list words used in the recognition test: classic choice = 1st, 8th, 10th
TEST_POSITIONS = [0, 7, 9]

MODALITIES = ['visual_words', 'auditory_words', 'pictures']

ITEM_TYPES = {
    'studied': 'studied word (correct answer: old)',
    'critical_lure': 'critical lure of a studied list (never shown; "old" = false memory)',
    'unstudied_word': 'word from a list that was NOT studied (correct answer: new)',
    'control_lure': 'critical lure of a list that was NOT studied (baseline for false memory)',
}


def check_materials():
    """Return a list of problems in the materials (empty list = OK)."""
    problems = []
    all_words = []
    for lure, words in DRM_LISTS.items():
        if len(words) != 12:
            problems.append(f'list {lure} has {len(words)} words instead of 12')
        if lure in words:
            problems.append(f'list {lure} contains its own critical lure')
        all_words += words
    duplicates = {w for w in all_words if all_words.count(w) > 1}
    if duplicates:
        problems.append(f'words appearing in more than one list: {sorted(duplicates)}')
    lures_in_lists = set(DRM_LISTS) & set(all_words)
    if lures_in_lists:
        problems.append(f'critical lures that appear as list words: {sorted(lures_in_lists)}')
    sets = LIST_SETS['A'] + LIST_SETS['B']
    if sorted(sets) != sorted(DRM_LISTS):
        problems.append('LIST_SETS must contain every list exactly once')
    return problems


def assign_conditions(participant_index, modality_setting, rng):
    """
    Balanced assignment based on the participant's position in the session (1, 2, 3, ...).
    - list set alternates A, B, A, B ...
    - modality: fixed by the session setting, or rotated across the 3 modalities when 'random',
      so that every combination of modality x list set is filled evenly.
    """
    list_set = 'A' if participant_index % 2 == 1 else 'B'
    if modality_setting == 'random':
        modality = MODALITIES[((participant_index - 1) // 2) % len(MODALITIES)]
    else:
        if modality_setting not in MODALITIES:
            raise ValueError(f'unknown modality: {modality_setting}')
        modality = modality_setting
    studied = LIST_SETS[list_set][:]
    rng.shuffle(studied)
    return dict(list_set=list_set, modality=modality, studied_lists=studied)


def build_test_items(studied_lists, rng):
    """Recognition test: 4 items per list (3 list words + critical lure), all 12 lists, shuffled."""
    items = []
    for lure, words in DRM_LISTS.items():
        studied = lure in studied_lists
        for pos in TEST_POSITIONS:
            items.append(dict(item=words[pos], list_id=lure,
                              item_type='studied' if studied else 'unstudied_word'))
        items.append(dict(item=lure, list_id=lure,
                          item_type='critical_lure' if studied else 'control_lure'))
    rng.shuffle(items)
    for i, it in enumerate(items):
        it['order'] = i
    return items


def score(trials):
    """
    trials: list of dicts with item_type and response ('old'/'new').
    Returns the proportion of 'old' answers per item type and the corrected false memory index.
    """
    out = {}
    for t in ITEM_TYPES:
        sel = [x for x in trials if x['item_type'] == t]
        out[f'p_old_{t}'] = (sum(x['response'] == 'old' for x in sel) / len(sel)) if sel else None
    if out['p_old_critical_lure'] is not None and out['p_old_control_lure'] is not None:
        out['false_memory_corrected'] = out['p_old_critical_lure'] - out['p_old_control_lure']
    else:
        out['false_memory_corrected'] = None
    return out


def count_recall(recall_text, list_words, critical_lure):
    """Score free recall: number of correct list words and whether the critical lure was intruded."""
    tokens = {w.strip('.,;:!?"\'').lower() for w in recall_text.replace('\n', ' ').split()}
    tokens.discard('')
    correct = len(tokens & {w.lower() for w in list_words})
    intrusion = critical_lure.lower() in tokens
    return correct, intrusion


def make_arithmetic_problem(rng):
    b = rng.randint(2, 19)
    if rng.random() < 0.5:
        a = rng.randint(11, 49)
        return f'{a} + {b}', a + b
    a = rng.randint(b + 11, 60)   # result always positive (at least 11)
    return f'{a} - {b}', a - b
