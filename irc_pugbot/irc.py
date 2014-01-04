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
            self.channel = None
            self.stage_delay = None
        self.staging_task = None

    def init_bot(self, bot):
        self.bot = bot
        pug_type = self.bot.config.get('TF2_PUG_TYPE', PugType.highlander)
        if pug_type == PugType.highlander:
            self.pug = irc_pugbot.pug.Tf2HighlanderPug()
        elif pug_type == PugType.fours:
            self.pug = irc_pugbot.pug.Tf2FoursPug()
        else:
            raise NotImplementedError
        self.channel = self.bot.config['TF2_PUG_CHANNEL']
        self.stage_delay = self.bot.config.get('TF2_PUG_STAGE_DELAY', None)
        self.privmsg = functools.partial(bot.send_privmsg, self.channel)
        self.bot.add_handler('NICK', self.handle_nick)
        self.bot.add_command_handler('add', self.add_command, ['classes'], irc.command.LastParamType.list_)
        self.bot.add_command_handler('remove', self.remove_command)
        self.bot.add_command_handler('need', self.need_command)
        self.bot.add_command_handler('pick', self.pick_command, ['name', 'class_'])
        self.bot.add_command_handler('list', self.list_command, ['class_'])

    @asyncio.coroutine
    def add_command(self, bot, command):
        """Add yourself to the pug"""
        classes = [c.lower() for c in command.params.classes]
        captain = 'captain' in classes
        classes = [p for p in classes if p != 'captain']
        self.pug.add(command.sender, classes, captain)
        if self.pug.can_stage:
            self.do_staging_task()
        else:
            send_unstaged(self.privmsg, self.pug.unstaged_players)

    def do_staging_task(self):
        if not self.pug.staged_players:
            if not self.staging_task:
                if self.stage_delay:
                    self.privmsg('Staging pug in {0} seconds'.format(self.stage_delay))
                    self.staging_task = self.bot.loop.call_later(30, self.do_stage)
                else:
                    self.do_stage()

    def do_stage(self):
        self.pug.stage()
        team_msg = '{0} - {1}'
        self.privmsg('Captains: {0}'.format(', '.join(team_msg.format(COLORS[i].upper(), self.pug.captains[i]) for i in range(2))))
        self.privmsg('It is {0}\'s turn to pick'.format(self.pug.captains[self.pug.picking_team]))

    @asyncio.coroutine
    def remove_command(self, bot, command):
        """Remove yourself from the pug (prior to picking start)"""
        try:
            self.pug.remove(command.sender)
        except KeyError:
            pass
        else:
            send_unstaged(self.privmsg, self.pug.unstaged_players)
            if self.staging_task and not self.pug.can_stage():
                self.staging_task.cancel()

    @asyncio.coroutine
    def turn_command(self, bot, command):
        if self.pug.captains:
            self.privmsg('It is {0}\'s turn to pick.'.format(self.pug.captains[self.pug.picking_team]))
        else:
            self.privmsg('No pugs are currently picking')

    @asyncio.coroutine
    def pick_command(self, bot, command):
        """Pick player on a class"""
        if self.pug.staged_players is None:
            self.privmsg(bot, '{0}, pug is not ready for picking'.format(command.sender))
        elif command.sender not in self.pug.captains:
            self.privmsg(bot, '{0}, only captains can pick'.format(command.sender))
        elif command.sender != self.pug.captains[self.pug.picking_team]:
            self.privmsg('{0}, it is not your pick'.format(command.sender))
        else:
            self.pug.pick(command.params.name, command.params.class_.lower())
            if self.pug.can_start:
                teams = self.pug.make_game()
                send_teams_message(self.privmsg, teams)
                for i, team in enumerate(teams):
                    for class_, player in team:
                        self.bot.send_privmsg(player, PLAYER_MSG.format(class_=class_, team=COLORS[i].title()))
                if self.pug.can_stage:
                    self.do_staging_task()

    @asyncio.coroutine
    def need_command(self, bot, command):
        """Check what's needed to start the pug"""
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
    def list_command(self, bot, command):
        """List players for a class"""
        class_ = command.params.class_.lower()
        if self.pug.staged_players and command.sender in self.pug.staged_players:
            players = [p for p, (cs, _) in self.pug.staged_players.items() if class_ in cs]
        else:
            players = [p for p, (cs, _) in self.pug.unstaged_players.items() if class_ in cs]
        self.privmsg('{0}s: {1}'.format(class_, ', '.join(players)))

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