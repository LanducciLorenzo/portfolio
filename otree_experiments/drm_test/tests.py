from otree.api import Bot, expect, Submission
from . import *


def call_live_method(method, **kwargs):
    # answer every item: 'old' to studied words and critical lures, 'new' to everything else
    data = method(1, {'type': 'load'})[1]
    method(1, {'type': 'answer', 'order': -1, 'response': 'old', 'confidence': 4})   # invalid: ignored
    while not data['done']:
        data = method(1, {'type': 'answer', 'order': data['order'], 'response': 'old',
                          'confidence': 3, 'rt_ms': 900})[1]


class PlayerBot(Bot):
    def play_round(self):
        yield Submission(Recognition, check_html=False)
        expect(self.player.progress, 48)
        expect(self.player.p_old_studied, 1)
        expect(self.player.false_memory_corrected, 0)   # everything answered 'old' -> no difference
