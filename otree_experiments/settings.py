from os import environ

SESSION_CONFIGS = [
    # ---------- Experiment 1: public goods game, 2x2 design ----------
    # endowments (equal / unequal) x matching (partner = fixed groups / stranger = new groups every round)
    dict(name='pgg_equal_partner', display_name='PGG - EQUAL endowments - fixed groups',
         app_sequence=['pgg_inequality'], num_demo_participants=4,
         treatment='equal', matching='partner'),
    dict(name='pgg_unequal_partner', display_name='PGG - UNEQUAL endowments - fixed groups',
         app_sequence=['pgg_inequality'], num_demo_participants=4,
         treatment='unequal', matching='partner'),
    dict(name='pgg_equal_stranger', display_name='PGG - EQUAL endowments - new groups every round',
         app_sequence=['pgg_inequality'], num_demo_participants=8,
         treatment='equal', matching='stranger'),
    dict(name='pgg_unequal_stranger', display_name='PGG - UNEQUAL endowments - new groups every round',
         app_sequence=['pgg_inequality'], num_demo_participants=8,
         treatment='unequal', matching='stranger'),

    # ---------- Experiment 2: DRM false memory, online version ----------
    dict(name='drm_memory', display_name='DRM false memory (modality assigned at random)',
         app_sequence=['drm_intro', 'drm_study', 'drm_distractor', 'drm_test', 'drm_questionnaire'],
         num_demo_participants=3,
         modality='random',        # 'random', 'visual_words', 'auditory_words' or 'pictures'
         free_recall=True,         # free recall after each studied list
         word_ms=1500,             # how long each item is shown (ms)
         gap_ms=500,               # blank interval between items (ms)
         recall_seconds=60,        # time for free recall after each list
         distractor_seconds=120,   # duration of the arithmetic distractor task
         participation_fee=0),
    dict(name='drm_visual_words', display_name='DRM - visual words only',
         app_sequence=['drm_intro', 'drm_study', 'drm_distractor', 'drm_test', 'drm_questionnaire'],
         num_demo_participants=1, modality='visual_words', free_recall=True,
         word_ms=1500, gap_ms=500, recall_seconds=60, distractor_seconds=120, participation_fee=0),
    dict(name='drm_auditory_words', display_name='DRM - auditory words only (browser speech)',
         app_sequence=['drm_intro', 'drm_study', 'drm_distractor', 'drm_test', 'drm_questionnaire'],
         num_demo_participants=1, modality='auditory_words', free_recall=True,
         word_ms=1500, gap_ms=500, recall_seconds=60, distractor_seconds=120, participation_fee=0),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.05,   # 1 point = 5 euro cents
    participation_fee=3.00,
    doc='',
)

# Data stored once per participant and shared across apps
PARTICIPANT_FIELDS = [
    'drm_modality',        # visual_words / auditory_words / pictures
    'drm_list_set',        # 'A' or 'B': which half of the lists is studied (counterbalancing)
    'drm_studied_lists',   # list ids studied, in presentation order
    'drm_test_items',      # recognition test items, in test order
]
SESSION_FIELDS = []

LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = True
POINTS_DECIMAL_PLACES = 2   # the PGG group share can be a decimal (e.g. 13 x 1.6 / 4 = 5.2)

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = 'Experiments by Lorenzo Landucci: public goods game and DRM false memory.'

SECRET_KEY = 'change-this-before-running-a-real-session'
INSTALLED_APPS = ['otree']
