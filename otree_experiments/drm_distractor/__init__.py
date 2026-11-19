from otree.api import *
import random
from drm_common.logic import make_arithmetic_problem

doc = """
DRM part 3: arithmetic distractor task between study and test (prevents rehearsal).
Problems are generated and checked on the server with live pages, so the score is reliable.
"""


class C(BaseConstants):
    NAME_IN_URL = 'drm_distractor'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    n_attempted = models.IntegerField(initial=0)
    n_correct = models.IntegerField(initial=0)
    current_answer = models.IntegerField()   # answer to the problem currently on screen


def new_problem(player: Player):
    rng = random.Random()
    text, answer = make_arithmetic_problem(rng)
    player.current_answer = answer
    return text


class Arithmetic(Page):
    @staticmethod
    def get_timeout_seconds(player: Player):
        return player.session.config.get('distractor_seconds', 120)

    @staticmethod
    def live_method(player: Player, data):
        if data.get('type') == 'answer' and player.field_maybe_none('current_answer') is not None:
            try:
                value = int(str(data.get('value', '')).strip())
            except ValueError:
                value = None
            player.n_attempted += 1
            if value == player.current_answer:
                player.n_correct += 1
        problem = new_problem(player)
        return {player.id_in_group: dict(problem=problem, correct=player.n_correct)}


page_sequence = [Arithmetic]
