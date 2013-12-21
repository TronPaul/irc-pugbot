import random

CLASSES = ['scout', 'soldier', 'pyro', 'demoman', 'heavy', 'engineer', 'medic', 'sniper', 'spy']


class MissingClassError(ValueError):
    pass


def random_captains(players):
    all_captains = [nick for (nick, (_, captain)) in players.items() if captain]
    return random.sample(all_captains, 2)


def can_stage_highlander(players):
        class_count = {c: 0 for c in CLASSES}
        captain_count = 0
        for nick, (classes, captain) in players.items():
            if captain:
                captain_count += 1
            for class_ in classes:
                class_count[class_] += 1
        # TODO: make smarter
        return captain_count > 1 and all([v > 1 for v in class_count.values()])


class Tf2Pug:
    allowed_classes = CLASSES

    def __init__(self):
        self.unstaged_players = {}
        self.staged_players = {}
        self.captains = None

    @property
    def can_stage(self):
        return can_stage_highlander(self.unstaged_players)

    def add(self, nick, classes, captain=False):
        for i, c in enumerate(classes):
            if c not in self.allowed_classes:
                # TODO: send warning on filter
                del classes[i]
        if not classes:
            raise MissingClassError
        self.unstaged_players[nick] = (classes, captain)

    def remove(self, nick):
        del self.unstaged_players[nick]

    def stage(self):
        self.staged_players = self.unstaged_players
        self.unstaged_players = {}
        self.captains = random_captains(self.staged_players)

    def pick(self, team, nick, class_):
        pass
