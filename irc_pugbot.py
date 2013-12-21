CLASSES = ['scout', 'soldier', 'pyro', 'demoman', 'heavy', 'engineer', 'medic', 'sniper', 'spy']


class MissingClassError(ValueError):
    pass


class Tf2Pug:
    allowed_classes = CLASSES

    def __init__(self):
        self.unstaged_players = {}

    @property
    def can_stage(self):
        class_count = {c: 0 for c in self.allowed_classes}
        captain_count = 0
        for nick, (classes, captain) in self.unstaged_players.items():
            if captain:
                captain_count += 1
            for class_ in classes:
                class_count[class_] += 1
        # TODO: make smarter
        return captain_count > 1 and all([v > 1 for v in class_count.values()])

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

    def pick(self, nick, class_):
        pass
