from otree.api import Bot, expect, SubmissionMustFail
from . import *


class PlayerBot(Bot):
    def play_round(self):
        yield SubmissionMustFail(Consent, dict(consent=False))
        yield Consent, dict(consent=True)
        yield Demographics, dict(age=28, gender='Prefer not to say', native_language='Italian',
                                 english_level='B2', device='Computer / laptop')
        if self.participant.drm_modality == 'auditory_words':
            yield SubmissionMustFail(SoundCheck, dict(sound_check='house'))
            yield SoundCheck, dict(sound_check='Garden')
        expect(len(self.participant.drm_test_items), 48)
        yield Instructions
