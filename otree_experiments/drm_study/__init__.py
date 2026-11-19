from otree.api import *
from drm_common.logic import DRM_LISTS, LIST_SETS, count_recall

doc = """
DRM part 2: study phase. One round per studied list.
Items are shown (or spoken) one at a time by JavaScript; the page then submits itself.
Optional free recall after each list, scored automatically (correct words + critical lure intrusion).
"""


class C(BaseConstants):
    NAME_IN_URL = 'drm_study'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = len(LIST_SETS['A'])   # 6 lists studied per participant


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    list_id = models.StringField()
    modality = models.StringField()
    presentation_completed = models.BooleanField(initial=False)
    presentation_ms = models.IntegerField()   # measured duration of the list in the browser
    page_hidden_count = models.IntegerField(initial=0)   # times the participant left the tab
    recall_text = models.LongStringField(blank=True, label='')
    recall_correct = models.IntegerField()
    recall_intrusion = models.BooleanField()


def current_list(player: Player):
    return player.participant.drm_studied_lists[player.round_number - 1]


def item_duration(session):
    return session.config.get('word_ms', 1500) + session.config.get('gap_ms', 500)


class StudyList(Page):
    form_model = 'player'
    form_fields = ['presentation_completed', 'presentation_ms', 'page_hidden_count']

    @staticmethod
    def get_timeout_seconds(player: Player):
        n = len(DRM_LISTS[current_list(player)])
        # list duration + time to press Start; after this the page submits anyway
        return n * item_duration(player.session) / 1000 + 90

    @staticmethod
    def js_vars(player: Player):
        config = player.session.config
        return dict(
            words=DRM_LISTS[current_list(player)],
            modality=player.participant.drm_modality,
            word_ms=config.get('word_ms', 1500),
            gap_ms=config.get('gap_ms', 500),
        )

    @staticmethod
    def vars_for_template(player: Player):
        return dict(n_list=player.round_number, n_total=C.NUM_ROUNDS)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.list_id = current_list(player)
        player.modality = player.participant.drm_modality
        if timeout_happened:
            player.presentation_completed = False


class FreeRecall(Page):
    form_model = 'player'
    form_fields = ['recall_text']

    @staticmethod
    def is_displayed(player: Player):
        return player.session.config.get('free_recall', True)

    @staticmethod
    def get_timeout_seconds(player: Player):
        return player.session.config.get('recall_seconds', 60)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        lure = current_list(player)
        correct, intrusion = count_recall(player.recall_text or '', DRM_LISTS[lure], lure)
        player.recall_correct = correct
        player.recall_intrusion = intrusion


page_sequence = [StudyList, FreeRecall]
