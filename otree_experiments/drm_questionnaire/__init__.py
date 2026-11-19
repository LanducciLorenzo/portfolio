from otree.api import *
from drm_common.questionnaire_items import ITEMS, ITEM_DIMENSION, REVERSED, SCALE_LABELS

doc = """
DRM part 5: visual-verbal cognitive style questionnaire, attention check, awareness questions, debriefing.
Computes a visual score, a verbal score and a visual-minus-verbal index.
"""


class C(BaseConstants):
    NAME_IN_URL = 'drm_questionnaire'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    N_ITEMS = len(ITEMS)


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


def likert(i):
    return models.IntegerField(
        label=ITEMS[i - 1],
        choices=[[k + 1, lab] for k, lab in enumerate(SCALE_LABELS)],
        widget=widgets.RadioSelectHorizontal,
    )


class Player(BasePlayer):
    vv1 = likert(1)
    vv2 = likert(2)
    vv3 = likert(3)
    vv4 = likert(4)
    vv5 = likert(5)
    vv6 = likert(6)
    vv7 = likert(7)
    vv8 = likert(8)
    vv9 = likert(9)
    vv10 = likert(10)
    attention_check = models.IntegerField(
        label='To show that you are reading carefully, please select "2 Disagree" for this statement.',
        choices=[[k + 1, lab] for k, lab in enumerate(SCALE_LABELS)],
        widget=widgets.RadioSelectHorizontal,
    )
    attention_passed = models.BooleanField()
    visual_score = models.FloatField()
    verbal_score = models.FloatField()
    visual_minus_verbal = models.FloatField()
    noticed_theme = models.StringField(
        label='Did you notice that the words in each list were related to one common word that was never presented?',
        choices=['Yes, during the lists', 'Yes, during the final test', 'No'],
        widget=widgets.RadioSelect,
    )
    used_notes = models.BooleanField(
        label='Did you write down any words during the lists? (Please be honest: it does not affect anything.)',
        widget=widgets.RadioSelect,
    )
    comments = models.LongStringField(blank=True, label='Any comments about the study? (optional)')


def compute_scores(player: Player):
    visual, verbal = [], []
    for i in range(1, C.N_ITEMS + 1):
        value = getattr(player, f'vv{i}')
        if i in REVERSED:
            value = 6 - value
        (visual if ITEM_DIMENSION[i - 1] == 'visual' else verbal).append(value)
    player.visual_score = sum(visual) / len(visual)
    player.verbal_score = sum(verbal) / len(verbal)
    player.visual_minus_verbal = player.visual_score - player.verbal_score
    player.attention_passed = player.attention_check == 2


class StyleQuestionnaire(Page):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player: Player):
        fields = [f'vv{i}' for i in range(1, C.N_ITEMS + 1)]
        fields.insert(5, 'attention_check')   # attention check hidden in the middle
        return fields

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        compute_scores(player)


class Awareness(Page):
    form_model = 'player'
    form_fields = ['noticed_theme', 'used_notes', 'comments']


class Debriefing(Page):
    @staticmethod
    def vars_for_template(player: Player):
        test = player.participant.drm_test_items
        lures = sorted({it['list_id'] for it in test if it['item_type'] == 'critical_lure'})
        return dict(lures=lures)


page_sequence = [StyleQuestionnaire, Awareness, Debriefing]
