import enum
import asyncio
import functools
import irc_pugbot.pug
import irc.command

COLORS = ['red', 'blue']
PLAYER_MSG = 'You have been picked as {class_} for {color} team.'
TEAM_MSG = '{color} team: {players}'
CLASS_MSG = '{player} on {class_}'


class PugType(enum.Enum):
    highlander = 1
    fours = 2


def send_teams_message(privmsg, teams):
    for i, team in enumerate(teams):
        players = ', '.join([CLASS_MSG.format(p, c.title()) for c, p in team.items()])
        team_msg = TEAM_MSG.format(color=COLORS[i].title(), players=players)
        privmsg(team_msg)


def send_unstaged(privmsg, unstaged):
    privmsg('Players added: {0}'.format(', '.join(unstaged.keys())))


class IrcPug:
    def __init__(self, bot):
        if bot:
            self.init_bot(bot)
        else:
            self.bot = None
            self.pug = None

    def init_bot(self, bot):
        self.bot = bot
        pug_type = self.bot.config.get('TF2_PUG_TYPE', PugType.highlander)
        if pug_type == PugType.highlander:
            self.pug = irc_pugbot.pug.Tf2HighlanderPug()
        else:
            raise NotImplementedError
        self.channel = self.bot.config['TF2_PUG_CHANNEL']
        self.privmsg = functools.partial(bot.send_privmsg, self.channel)
        self.bot.add_handler('NICK', self.handle_nick)
        self.bot.add_command_handler('add', self.add_command, ['classes'], irc.command.LastParamType.list_)
        self.bot.add_command_handler('remove', self.remove_command)
        self.bot.add_command_handler('pick', self.pick_command, ['name', 'class_'])

    @asyncio.coroutine
    def add_command(self, bot, command):
        captain = 'captain' in command.params.classes
        classes = [p for p in command.params.classes if p != 'captain']
        self.pug.add(command.sender, classes, captain)
        if self.pug.can_stage:
            # TODO make stage be called after timeout
            self.pug.stage()
        else:
            send_unstaged(self.privmsg, self.pug.unstaged_players)

    @asyncio.coroutine
    def remove_command(self, bot, command):
        try:
            self.pug.remove(command.sender)
        except KeyError:
            pass
        else:
            send_unstaged(self.privmsg, self.pug.unstaged_players)

    @asyncio.coroutine
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

    @asyncio.coroutine
    def need_command(self, bot, command):
        captain_need_count, player_need_count, class_need_count = self.pug.need
        base_need_msg = 'Need:'
        need_parts = []
        if class_need_count:
            need_parts.extend('{0}: {1}'.format(k, v) for k, v in class_need_count.items())
        if captain_need_count:
            need_parts.append('captain: {0}'.format(captain_need_count))
        if player_need_count:
            need_parts.append('players: {0}'.format(player_need_count))
        need_msg = '{0} {1}'.format(base_need_msg, ', '.join(need_parts))
        self.privmsg(need_msg)

    @asyncio.coroutine
    def handle_nick(self, bot, message):
        old_nick = message.nick
        new_nick = message.params[0]
        if old_nick in self.pug.unstaged_players:
            player_info = self.pug.unstaged_players.pop(old_nick)
            self.pug.unstaged_players[new_nick] = player_info
        if old_nick in self.pug.staged_players:
            player_info = self.pug.staged_players.pop(old_nick)
            self.pug.staged_players[new_nick] = player_info
        if old_nick in self.pug.captains:
            i = self.pug.captains.index(old_nick)
            self.pug.captains[i] = new_nick
        for team in self.pug.teams:
            for class_, nick in team.items():
                if old_nick == nick:
                    team[class_] = new_nick