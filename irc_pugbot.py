import random
import functools

CLASSES = ['scout', 'soldier', 'pyro', 'demoman', 'heavy', 'engineer', 'medic', 'sniper', 'spy']
COLORS = ['red', 'blue']
PLAYER_MSG = 'You have been picked as {class_} for {color} team.'
TEAM_MSG = '{color} team: {players}'
CLASS_MSG = '{player} on {class_}'


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


def river():
    team = 0
    yield team % 2
    while True:
        team += 1
        yield team % 2
        yield team % 2


def send_teams_message(privmsg, teams):
    for i, team in enumerate(teams):
        players = ', '.join([CLASS_MSG.format(p, c.title()) for c, p in team.items()])
        team_msg = TEAM_MSG.format(color=COLORS[i].title(), players=players)
        privmsg(team_msg)


class IrcTf2Pug:
    def __init__(self, bot):
        if bot:
            self.init_bot(bot)
        else:
            self.bot = None
            self.pug = None

    def init_bot(self, bot):
        self.bot = bot
        self.pug = Tf2Pug()
        self.channel = self.bot.config['TF2_PUG_CHANNEL']
        self.privmsg = functools.partial(bot.send_privmsg, self.channel)
        self.bot.add_command_handler('add', self.add_command)
        self.bot.add_command_handler('remove', self.remove_command)
        self.bot.add_command_handler('pick', self.pick_command)

    def add_command(self, bot, command):
        captain = 'captain' in command.params
        classes = [p for p in command.params if p != 'captain']
        self.pug.add(command.sender, classes, captain)
        if self.pug.can_stage:
            self.pug.stage()

    def remove_command(self, bot, command):
        self.pug.remove(command.sender)

    def pick_command(self, bot, command):
        if self.pug.staged_players is None:
            self.privmsg(bot, '{0}, pug is not ready for picking'.format(command.sender))
        elif command.sender not in self.pug.captains:
            self.privmsg(bot, '{0}, only captains can pick'.format(command.sender))
        elif command.sender != self.pug.captains[self.pug.picking_team]:
            self.privmsg('{0}, it is not your pick'.format(command.sender))
        else:
            self.pug.pick(command.params[0], command.params[1])
            if self.pug.can_start:
                teams = self.pug.make_game()
                send_teams_message(self.privmsg, teams)
                for i, team in enumerate(teams):
                    for class_, player in team:
                        self.bot.send_privmsg(player, PLAYER_MSG.format(class_=class_, team=COLORS[i].title()))


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
            for c in CLASSES:
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