import asyncio
import functools
import irc_pugbot.pug

COLORS = ['red', 'blue']
PLAYER_MSG = 'You have been picked as {class_} for {color} team.'
TEAM_MSG = '{color} team: {players}'
CLASS_MSG = '{player} on {class_}'


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
        self.pug = irc_pugbot.pug.Tf2Pug()
        self.channel = self.bot.config['TF2_PUG_CHANNEL']
        self.privmsg = functools.partial(bot.send_privmsg, self.channel)
        self.bot.add_message_handler('NICK', self.handle_nick)
        self.bot.add_command_handler('add', self.add_command)
        self.bot.add_command_handler('remove', self.remove_command)
        self.bot.add_command_handler('pick', self.pick_command)

    @asyncio.coroutine
    def add_command(self, bot, command):
        captain = 'captain' in command.params
        classes = [p for p in command.params if p != 'captain']
        self.pug.add(command.sender, classes, captain)
        if self.pug.can_stage:
            # TODO make stage be called after timeout
            self.pug.stage()
        else:
            send_unstaged(self.privmsg, self.pug.unstaged_players)

    @asyncio.coroutine
    def remove_command(self, bot, command):
        self.pug.remove(command.sender)
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