from otree.api import Bot, expect, cu, SubmissionMustFail
from . import *
import random


class PlayerBot(Bot):
    def play_round(self):
        if self.round_number == 1:
            yield Introduction
            # a wrong answer must be rejected, then the correct one accepted
            yield SubmissionMustFail(Comprehension, dict(quiz_group_share=10, quiz_keep_all=0))
            yield Comprehension, dict(quiz_group_share=16, quiz_keep_all=self.player.endowment)
        yield Contribute, dict(contribution=random.randint(0, self.player.endowment))
        expect(self.player.payoff, '>=', 0)
        expect(self.player.contribution_share, '<=', 1)
        yield Results
        if self.round_number == C.NUM_ROUNDS:
            yield FinalQuestionnaire, dict(age=25, gender='Prefer not to say', strategy='test')
            # Payment is the last page and has no next button, so the bot does not submit it
