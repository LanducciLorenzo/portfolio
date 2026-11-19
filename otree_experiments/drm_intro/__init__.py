from otree.api import *
import random
from drm_common.logic import assign_conditions, build_test_items

doc = """
DRM false memory experiment - part 1: consent, demographics, instructions.
Assigns each participant a presentation modality and a counterbalanced list set.
"""


class C(BaseConstants):
    NAME_IN_URL = 'drm_intro'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    config = subsession.session.config
    for player in subsession.get_players():
        participant = player.participant
        # seed per participant: the assignment is reproducible and independent across participants
        rng = random.Random(f'{subsession.session.code}-{participant.id_in_session}')
        cond = assign_conditions(participant.id_in_session, config.get('modality', 'random'), rng)
        participant.drm_modality = cond['modality']
        participant.drm_list_set = cond['list_set']
        participant.drm_studied_lists = cond['studied_lists']
        participant.drm_test_items = build_test_items(cond['studied_lists'], rng)
        player.modality = cond['modality']
        player.list_set = cond['list_set']


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    modality = models.StringField()
    list_set = models.StringField()
    consent = models.BooleanField(
        label='I have read the information above and I agree to take part in this study.',
        widget=widgets.CheckboxInput,
    )
    age = models.IntegerField(min=18, max=99, label='Your age')
    gender = models.StringField(
        choices=['Female', 'Male', 'Non-binary / other', 'Prefer not to say'],
        widget=widgets.RadioSelect, label='Your gender',
    )
    native_language = models.StringField(label='Your native language')
    english_level = models.StringField(
        choices=['Native speaker', 'C2', 'C1', 'B2', 'B1 or lower'],
        label='Your level of English',
    )
    device = models.StringField(
        choices=['Computer / laptop', 'Tablet', 'Phone'],
        widget=widgets.RadioSelect, label='Which device are you using?',
    )
    sound_check = models.StringField(
        blank=True,
        label='Type the word you heard (only if you pressed the "Play test sound" button):',
    )


def consent_error_message(player: Player, value):
    if not value:
        return 'You need to agree to take part in order to continue.'


class Consent(Page):
    form_model = 'player'
    form_fields = ['consent']


class Demographics(Page):
    form_model = 'player'
    form_fields = ['age', 'gender', 'native_language', 'english_level', 'device']


class SoundCheck(Page):
    """Only for the auditory condition: makes sure the browser can play speech."""
    form_model = 'player'
    form_fields = ['sound_check']

    @staticmethod
    def is_displayed(player: Player):
        return player.participant.drm_modality == 'auditory_words'

    @staticmethod
    def error_message(player: Player, values):
        if values['sound_check'].strip().lower() != 'garden':
            return 'Please press "Play test sound", listen, and type the word you heard. Check that your sound is on.'


class Instructions(Page):
    @staticmethod
    def vars_for_template(player: Player):
        config = player.session.config
        modality = player.participant.drm_modality
        return dict(
            is_auditory=modality == 'auditory_words',
            is_pictures=modality == 'pictures',
            n_lists=len(player.participant.drm_studied_lists),
            free_recall=config.get('free_recall', True),
        )


page_sequence = [Consent, Demographics, SoundCheck, Instructions]
