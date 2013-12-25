import unittest
import asyncio
import unittest.mock
import irc_pugbot.irc
import irc.bot


class IrcTest(unittest.TestCase):
    def test_add(self):
        mock = unittest.mock.MagicMock()
        mock.config['TF2_PUG_CHANNEL'] = '#channel'
        ip = irc_pugbot.irc.IrcPug(mock)
        task = asyncio.Task(ip.add_command(mock, irc.bot.Command('nick', 'add', '#channel', ['scout'])))
        asyncio.get_event_loop().run_until_complete(task)
        self.assertTrue('nick' in ip.pug.unstaged_players)
        self.assertEquals(ip.pug.unstaged_players['nick'], (['scout'], False))

    def test_add_captain(self):
        mock = unittest.mock.MagicMock()
        mock.config['TF2_PUG_CHANNEL'] = '#channel'
        ip = irc_pugbot.irc.IrcPug(mock)
        task = asyncio.Task(ip.add_command(mock, irc.bot.Command('nick', 'add', '#channel', ['scout', 'captain'])))
        asyncio.get_event_loop().run_until_complete(task)
        self.assertTrue('nick' in ip.pug.unstaged_players)
        self.assertEquals(ip.pug.unstaged_players['nick'], (['scout'], True))

    def test_remove(self):
        mock = unittest.mock.MagicMock()
        mock.config['TF2_PUG_CHANNEL'] = '#channel'
        ip = irc_pugbot.irc.IrcPug(mock)
        task = asyncio.Task(ip.add_command(mock, irc.bot.Command('nick', 'add', '#channel', ['scout'])))
        asyncio.get_event_loop().run_until_complete(task)
        task = asyncio.Task(ip.remove_command(mock, irc.bot.Command('nick', 'remove', '#channel', [])))
        asyncio.get_event_loop().run_until_complete(task)
        self.assertEquals(len(ip.pug.unstaged_players), 0)

    def test_remove_non_existent(self):
        mock = unittest.mock.MagicMock()
        mock.config['TF2_PUG_CHANNEL'] = '#channel'
        ip = irc_pugbot.irc.IrcPug(mock)
        task = asyncio.Task(ip.remove_command(mock, irc.bot.Command('nick', 'remove', '#channel', [])))
        asyncio.get_event_loop().run_until_complete(task)
        self.assertEquals(len(ip.pug.unstaged_players), 0)

    def test_pick(self):
        pass

    def test_pick_non_existent(self):
        pass

    def test_pick_already_picked_player(self):
        pass

    def test_pick_by_non_captain(self):
        pass

    def test_pick_by_wrong_captain(self):
        pass

    def test_pick_already_picked_class(self):
        pass

    def test_unstaged_nick_changes(self):
        pass

    def test_staged_nick_changes(self):
        pass

    def test_captains_nick_changes(self):
        pass

    def test_picked_nick_changes(self):
        pass