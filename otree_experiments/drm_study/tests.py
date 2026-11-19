from otree.api import Bot, expect, Submission
from . import *


class PlayerBot(Bot):
    def play_round(self):
        # the list is shown by JavaScript, so the bot submits the hidden fields directly
        yield Submission(StudyList, dict(presentation_completed=True, presentation_ms=24000,
                                         page_hidden_count=0), check_html=False)
        expect(self.player.list_id, self.participant.drm_studied_lists[self.round_number - 1])
        if self.session.config.get('free_recall', True):
            words = DRM_LISTS[self.player.list_id]
            # recall 3 correct words + the critical lure (an intrusion)
            text = ' '.join(words[:3] + [self.player.list_id])
            yield FreeRecall, dict(recall_text=text)
            expect(self.player.recall_correct, 3)
            expect(self.player.recall_intrusion, True)
