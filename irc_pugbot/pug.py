import random

CLASSES = ['scout', 'soldier', 'pyro', 'demoman', 'heavy', 'engineer', 'medic', 'sniper', 'spy']


class MissingClassError(ValueError):
    pass


class ClassAlreadyPickedError(ValueError):
    pass


def random_captains(players):
    all_captains = [nick for (nick, (_, captain)) in players.items() if captain]
    return random.sample(all_captains, 2)


def need_highlander(players):
        class_count = {c: 2 for c in CLASSES}
        captain_count = 2
        for nick, (classes, captain) in players.items():
            if captain and captain_count > 0:
                captain_count -= 1
            for class_ in classes:
                if class_count[class_] > 0:
                    class_count[class_] -= 1
        class_count = {class_: count for class_, count in class_count.items() if count > 0}
        return captain_count, class_count


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


def can_start_highlander(teams):
    return all([len(teams[i]) == 8 for i in range(2)])


def river():
    team = 0
    yield team % 2
    while True:
        team += 1
        yield team % 2
        yield team % 2


class Tf2Pug:
    allowed_classes = CLASSES

    def __init__(self):
        self.unstaged_players = {}
        self.staged_players = None
        self.captains = None
        self.teams = None
        self.order = None
        self.picking_team = None

    @property
    def can_stage(self):
        return can_stage_highlander(self.unstaged_players)

    @property
    def can_start(self):
        return can_start_highlander(self.teams)

    @property
    def need(self):
        return need_highlander(self.unstaged_players)

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
        assert self.can_stage
        self.staged_players = self.unstaged_players
        self.captains = random_captains(self.staged_players)
        [self.staged_players.pop(c) for c in self.captains]
        self.unstaged_players = {}
        self.teams = [{}, {}]
        self.order = river()
        self.picking_team = next(self.order)

    def pick(self, nick, class_):
        if class_ in self.teams[self.picking_team]:
            raise ClassAlreadyPickedError
        self.teams[self.picking_team][class_] = nick
        del self.staged_players[nick]
        self.picking_team = next(self.order)

    def make_game(self):
        assert self.can_start
        for captain, team in zip(self.captains, self.teams):
            for c in self.allowed_classes:
                if c not in team:
                    team[c] = captain
        teams = self.teams
        self.teams = None
        self.unstaged_players.update(self.staged_players)
        self.staged_players = None
        self.captains = None
        self.order = None
        self.picking_team = None
        return teams