from otree.api import *
from drm_common.logic import score

doc = """
DRM part 4: recognition test.
48 items (12 lists x 4): studied words, critical lures, words of unstudied lists, control lures.
For each item: old/new + confidence (1-4) + response time measured in the browser.
Every answer is saved immediately on the server (live page), so a page refresh does not lose data
and the test continues from where it stopped.
"""


class C(BaseConstants):
    NAME_IN_URL = 'drm_test'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    progress = models.IntegerField(initial=0)     # number of items answered
    n_items = models.IntegerField()
    # summary scores, computed when the test is finished
    p_old_studied = models.FloatField()           # hit rate
    p_old_critical_lure = models.FloatField()     # false memory
    p_old_unstudied_word = models.FloatField()    # false alarms to unrelated words
    p_old_control_lure = models.FloatField()      # baseline for critical lures
    false_memory_corrected = models.FloatField()  # critical lure - control lure


class Trial(ExtraModel):
    player = models.Link(Player)
    order = models.IntegerField()
    item = models.StringField()
    item_type = models.StringField()
    list_id = models.StringField()
    response = models.StringField()      # 'old' or 'new'
    confidence = models.IntegerField()   # 1 = guessing ... 4 = completely sure
    rt_ms = models.IntegerField()        # from word onset to old/new click


def items(player: Player):
    return player.participant.drm_test_items


def item_payload(player: Player):
    its = items(player)
    if player.progress >= len(its):
        return dict(done=True)
    it = its[player.progress]
    return dict(done=False, word=it['item'], order=it['order'],
                position=player.progress + 1, total=len(its))


def finish(player: Player):
    trials = [dict(item_type=t.item_type, response=t.response) for t in Trial.filter(player=player)]
    s = score(trials)
    for key, value in s.items():
        if value is not None:
            setattr(player, key, value)


class Recognition(Page):
    @staticmethod
    def live_method(player: Player, data):
        its = items(player)
        player.n_items = len(its)
        if data.get('type') == 'answer':
            expected = its[player.progress]['order'] if player.progress < len(its) else None
            # accept only the answer to the item on screen (ignores double clicks and old messages)
            valid = (
                expected is not None
                and data.get('order') == expected
                and data.get('response') in ('old', 'new')
                and data.get('confidence') in (1, 2, 3, 4)
            )
            if valid:
                it = its[player.progress]
                Trial.create(
                    player=player, order=it['order'], item=it['item'], item_type=it['item_type'],
                    list_id=it['list_id'], response=data['response'],
                    confidence=data['confidence'], rt_ms=int(data.get('rt_ms') or 0),
                )
                player.progress += 1
                if player.progress == len(its):
                    finish(player)
        return {player.id_in_group: item_payload(player)}

    @staticmethod
    def error_message(player: Player, values):
        if player.progress < len(items(player)):
            return 'Please answer all the words before continuing.'


def custom_export(players):
    """Long-format data: one row per recognition trial (Data page > Custom export)."""
    yield ['session', 'participant', 'modality', 'list_set', 'order', 'item', 'item_type',
           'list_id', 'response', 'confidence', 'rt_ms']
    for p in players:
        participant = p.participant
        for t in Trial.filter(player=p):
            yield [p.session.code, participant.code, participant.drm_modality, participant.drm_list_set,
                   t.order, t.item, t.item_type, t.list_id, t.response, t.confidence, t.rt_ms]


page_sequence = [Recognition]
