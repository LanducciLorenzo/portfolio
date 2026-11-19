from otree.api import Bot, expect, Submission
from . import *


def call_live_method(method, **kwargs):
    method(1, {'type': 'start'})
    for _ in range(5):
        method(1, {'type': 'answer', 'value': '0'})


class PlayerBot(Bot):
    def play_round(self):
        yield Submission(Arithmetic, check_html=False)
        expect(self.player.n_attempted, 5)
