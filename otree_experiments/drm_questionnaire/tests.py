from otree.api import Bot, expect
from . import *


class PlayerBot(Bot):
    def play_round(self):
        answers = {f'vv{i}': 4 if i % 2 else 2 for i in range(1, C.N_ITEMS + 1)}
        answers['attention_check'] = 2
        yield StyleQuestionnaire, answers
        expect(self.player.attention_passed, True)
        expect(self.player.visual_minus_verbal, 2)
        yield Awareness, dict(noticed_theme='No', used_notes=False, comments='')
