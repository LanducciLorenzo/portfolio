from otree.api import *

doc = """
Linear public goods game with a 2x2 design.
Research question: does inequality in initial endowments reduce cooperation?
- Endowments: EQUAL (20, 20, 20, 20) or UNEQUAL (10, 10, 30, 30). Same group total (80).
- Matching: PARTNER (same group in every round) or STRANGER (new random group every round).
Each player keeps the same endowment in every round, also under stranger matching.
Every choice marked 'DESIGN' is a researcher decision.
"""


class C(BaseConstants):
    NAME_IN_URL = 'pgg_inequality'
    PLAYERS_PER_GROUP = 4          # DESIGN: group size
    NUM_ROUNDS = 10                # DESIGN: number of rounds
    MULTIPLIER = 1.6               # DESIGN: must be > 1 and < PLAYERS_PER_GROUP
    MPCR = MULTIPLIER / PLAYERS_PER_GROUP   # marginal per capita return (0.4)
    ENDOWMENTS = dict(             # DESIGN: endowment per position in the group
        equal=[20, 20, 20, 20],
        unequal=[10, 10, 30, 30],
    )
    SHOW_OTHERS_ENDOWMENTS = True  # DESIGN: players see the other members' endowments
    DECISION_TIMEOUT = 120         # seconds; if a player does not decide, contribution = 0 (flagged)
    # Comprehension check (example: every member contributes 10 points)
    QUIZ_EXAMPLE_CONTRIBUTION = 10


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    config = subsession.session.config
    treatment = config.get('treatment', 'equal')
    matching = config.get('matching', 'partner')
    if subsession.round_number == 1:
        subsession.group_randomly()
    elif matching == 'stranger':
        # new random groups, but every player keeps the same position, hence the same endowment
        subsession.group_randomly(fixed_id_in_group=True)
    else:
        subsession.group_like_round(1)
    endowments = C.ENDOWMENTS[treatment]
    high = max(endowments)
    for player in subsession.get_players():
        player.treatment = treatment
        player.matching = matching
        player.endowment = endowments[player.id_in_group - 1]
        player.is_high_endowment = treatment == 'unequal' and player.endowment == high


class Group(BaseGroup):
    total_contribution = models.IntegerField()
    individual_share = models.CurrencyField()


class Player(BasePlayer):
    treatment = models.StringField()
    matching = models.StringField()
    endowment = models.IntegerField()
    is_high_endowment = models.BooleanField()
    contribution = models.IntegerField(
        min=0, label='How many points do you want to contribute to the group project?'
    )
    contribution_share = models.FloatField()   # contribution / endowment (0 to 1)
    timed_out = models.BooleanField(initial=False)
    # comprehension check, answered once in round 1
    quiz_group_share = models.FloatField(
        label='Suppose every member of your group contributes 10 points. '
              'How many points does EACH member receive from the group project?'
    )
    quiz_keep_all = models.IntegerField(
        label='Suppose you contribute 0 points. How many of your own points do you keep this round?'
    )
    # final questionnaire (last round)
    age = models.IntegerField(min=18, max=99, label='Your age')
    gender = models.StringField(
        choices=['Female', 'Male', 'Non-binary / other', 'Prefer not to say'],
        label='Your gender', widget=widgets.RadioSelect,
    )
    strategy = models.LongStringField(blank=True, label='Briefly, how did you decide how much to contribute?')


def contribution_max(player: Player):
    return player.endowment


def quiz_group_share_error_message(player: Player, value):
    correct = C.QUIZ_EXAMPLE_CONTRIBUTION * C.PLAYERS_PER_GROUP * C.MULTIPLIER / C.PLAYERS_PER_GROUP
    if abs(value - correct) > 0.01:
        return ('Not quite. All contributions are added up, multiplied by {} and then divided equally '
                'among the {} members. Try again.'.format(C.MULTIPLIER, C.PLAYERS_PER_GROUP))


def quiz_keep_all_error_message(player: Player, value):
    if value != player.endowment:
        return 'Not quite. The points you do not contribute stay with you. Try again.'


def set_payoffs(group: Group):
    players = group.get_players()
    group.total_contribution = sum(p.contribution for p in players)
    group.individual_share = cu(group.total_contribution * C.MULTIPLIER / C.PLAYERS_PER_GROUP)
    for p in players:
        p.payoff = cu(p.endowment - p.contribution) + group.individual_share
        p.contribution_share = p.contribution / p.endowment


# PAGES
class Introduction(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Comprehension(Page):
    form_model = 'player'
    form_fields = ['quiz_group_share', 'quiz_keep_all']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Contribute(Page):
    form_model = 'player'
    form_fields = ['contribution']
    timeout_seconds = C.DECISION_TIMEOUT

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            others_endowments=[p.endowment for p in player.get_others_in_group()],
            show_others=C.SHOW_OTHERS_ENDOWMENTS,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            player.contribution = 0
            player.timed_out = True


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs


class Results(Page):
    timeout_seconds = 60   # avoids a whole group waiting for one inactive player

    @staticmethod
    def vars_for_template(player: Player):
        history = [
            dict(round=p.round_number, endowment=p.endowment, contribution=p.contribution,
                 group_total=p.group.total_contribution, payoff=p.payoff)
            for p in player.in_all_rounds()
        ]
        return dict(
            others=[(p.endowment, p.contribution) for p in player.get_others_in_group()],
            kept=player.endowment - player.contribution,
            history=history,
        )


class FinalQuestionnaire(Page):
    form_model = 'player'
    form_fields = ['age', 'gender', 'strategy']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


class Payment(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        participant = player.participant
        return dict(
            total_points=participant.payoff,
            total_money=participant.payoff_plus_participation_fee(),
        )


page_sequence = [Introduction, Comprehension, Contribute, ResultsWaitPage, Results,
                 FinalQuestionnaire, Payment]
