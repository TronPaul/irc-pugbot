CLASSES = ['scout', 'soldier', 'pyro', 'demoman', 'heavy', 'engineer', 'medic', 'sniper', 'spy']


class Tf2Pug:
    allowed_classes = CLASSES

    def __init__(self):
        self.unstaged_players = {}

    def add(self, nick, classes):
        for i, c in enumerate(classes):
            if c not in self.allowed_classes:
                # TODO: send warning on filter
                del classes[i]
        self.unstaged_players[nick] = classes

    def remove(self, nick):
        pass

    def pick(self, nick, class_):
        pass
