import random

CLASSES = ['scout', 'soldier', 'pyro', 'demoman', 'heavy', 'engineer', 'medic', 'sniper', 'spy']


class MissingClassError(ValueError):
    pass


class ClassAlreadyPickedError(ValueError):
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


def can_start_highlander(teams):
    return all([len(teams[i]) == 8 for i in range(2)])


class IrcTf2Pug:
    def __init__(self, bot):
        if bot:
            self.init_bot(bot)
        else:
            self.bot = None

    def init_bot(self, bot):
        self.bot = bot
        self.pug = Tf2Pug()


class Tf2Pug:
    allowed_classes = CLASSES

    def __init__(self):
        self.unstaged_players = {}
        self.staged_players = {}
        self.captains = None
        self.teams = None

    @property
    def can_stage(self):
        return can_stage_highlander(self.unstaged_players)

    @property
    def can_start(self):
        return can_start_highlander(self.teams)

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
        self.captains = random_captains(self.staged_players)
        [self.unstaged_players.pop(c) for c in self.captains]
        self.staged_players = self.unstaged_players
        self.unstaged_players = {}
        self.teams = [{}, {}]

    def pick(self, team, nick, class_):
        if class_ in self.teams[team]:
            raise ClassAlreadyPickedError
        self.teams[team][class_] = nick
        del self.staged_players[nick]

    def make_game(self):
        for captain, team in zip(self.captains, self.teams):
            for c in CLASSES:
                if c not in team:
                    team[c] = captain
        teams = self.teams
        self.teams = None
        self.unstaged_players.update(self.staged_players)
        self.staged_players = {}
        self.captains = None
        return teams