"""Tests for the DRM logic that do not need oTree. Run with:  python tests/test_logic.py"""
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from drm_common.logic import (DRM_LISTS, LIST_SETS, MODALITIES, assign_conditions, build_test_items,
                              check_materials, count_recall, make_arithmetic_problem, score)


def test_materials():
    assert check_materials() == [], check_materials()


def test_assignment_is_balanced():
    rng = random.Random(1)
    combos = Counter()
    for i in range(1, 61):
        c = assign_conditions(i, 'random', rng)
        combos[(c['modality'], c['list_set'])] += 1
        assert sorted(c['studied_lists']) == sorted(LIST_SETS[c['list_set']])
    assert len(combos) == 6 and set(combos.values()) == {10}, combos


def test_fixed_modality():
    c = assign_conditions(5, 'visual_words', random.Random(0))
    assert c['modality'] == 'visual_words'
    try:
        assign_conditions(1, 'smell', random.Random(0))
        raise AssertionError('unknown modality accepted')
    except ValueError:
        pass


def test_test_items():
    rng = random.Random(2)
    studied = LIST_SETS['A']
    items = build_test_items(studied, rng)
    assert len(items) == 48
    types = Counter(it['item_type'] for it in items)
    assert types == {'studied': 18, 'critical_lure': 6, 'unstudied_word': 18, 'control_lure': 6}, types
    assert len({it['item'] for it in items}) == 48           # no word tested twice
    assert [it['order'] for it in items] == list(range(48))
    for it in items:
        if it['item_type'] in ('critical_lure', 'control_lure'):
            assert it['item'] == it['list_id']
        else:
            assert it['item'] in DRM_LISTS[it['list_id']]
        assert (it['list_id'] in studied) == (it['item_type'] in ('studied', 'critical_lure'))


def test_score():
    trials = ([dict(item_type='studied', response='old')] * 3 + [dict(item_type='studied', response='new')]
              + [dict(item_type='critical_lure', response='old')] * 2 + [dict(item_type='critical_lure', response='new')] * 2
              + [dict(item_type='unstudied_word', response='new')] * 4
              + [dict(item_type='control_lure', response='old')] + [dict(item_type='control_lure', response='new')] * 3)
    s = score(trials)
    assert s['p_old_studied'] == 0.75 and s['p_old_critical_lure'] == 0.5
    assert s['p_old_unstudied_word'] == 0 and s['p_old_control_lure'] == 0.25
    assert s['false_memory_corrected'] == 0.25
    assert score([])['false_memory_corrected'] is None


def test_recall():
    words = DRM_LISTS['sleep']
    assert count_recall('Bed, rest\nAWAKE sleep sleep', words, 'sleep') == (3, True)
    assert count_recall('', words, 'sleep') == (0, False)
    assert count_recall('bedroom resting', words, 'sleep') == (0, False)   # no partial matches


def test_arithmetic():
    rng = random.Random(3)
    for _ in range(200):
        text, answer = make_arithmetic_problem(rng)
        assert eval(text) == answer and answer > 0


if __name__ == '__main__':
    tests = [v for k, v in dict(globals()).items() if k.startswith('test_')]
    for t in tests:
        t()
        print('OK ', t.__name__)
    print(f'{len(tests)} tests passed')
