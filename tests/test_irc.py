import unittest
import asyncio
import itertools
import unittest.mock
import tests.utils
import irc_pugbot.irc
import irc.bot
import irc.command
import irc.messages
import irc.parser

CLASSES = ['scout', 'soldier', 'pyro', 'demoman', 'heavy', 'engineer', 'medic', 'sniper', 'spy']


class IrcTest(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

        self.b = irc.bot.IrcBot('irc.example.com', 'nick', loop=self.loop)
        self.b.config['TF2_PUG_CHANNEL'] = '#channel'
        self.ip = irc_pugbot.irc.IrcPug(self.b)

    def tearDown(self):
        self.loop.close()

    def create_patch(self, name, **config):
        patcher = unittest.mock.patch(name, **config)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def patch_connect(self, transport=None, protocol=None):
        if not transport:
            transport = unittest.mock.Mock()
        if not protocol:
            protocol = irc.parser.StreamProtocol(loop=self.loop)

        @asyncio.coroutine
        def gen(*args):
            return transport, protocol

        self.create_patch('irc.client._connect', new=gen)
        return transport, protocol

    def test_add(self):
        stream = irc.parser.StreamProtocol(loop=self.loop)
        stream.feed_data(irc.messages.PrivMsg('#channel', ';add scout', prefix='nick!Nick@example.com').encode())
        stream.feed_eof()

        transport, _ = self.patch_connect(protocol=stream)
        self.loop.run_until_complete(self.b.start())
        self.loop.run_until_complete(self.b._read_handler)
        self.loop.run_until_complete(asyncio.Task(self.b.tasks.join(), loop=self.loop))
        self.assertTrue('nick' in self.ip.pug.unstaged_players)
        self.assertEquals(self.ip.pug.unstaged_players['nick'], (['scout'], False))

    def test_add_captain(self):
        stream = irc.parser.StreamProtocol(loop=self.loop)
        stream.feed_data(irc.messages.PrivMsg('#channel', ';add scout captain', prefix='nick!Nick@example.com').encode())
        stream.feed_eof()

        transport, _ = self.patch_connect(protocol=stream)
        self.loop.run_until_complete(self.b.start())
        self.loop.run_until_complete(self.b._read_handler)
        self.loop.run_until_complete(asyncio.Task(self.b.tasks.join(), loop=self.loop))
        self.assertTrue('nick' in self.ip.pug.unstaged_players)
        self.assertEquals(self.ip.pug.unstaged_players['nick'], (['scout'], True))

    def test_add_stages_when_ready(self):
        stream = irc.parser.StreamProtocol(loop=self.loop)
        players = list(itertools.chain.from_iterable(tests.utils.generate_highlander_game()))
        for player in players:
            stream.feed_data(irc.messages.PrivMsg('#channel', ';add {0} captain'.format(' '.join(player.classes)), prefix='{0}!{1}@example.com'.format(player.nick, player.nick.title())).encode())
        stream.feed_eof()
        self.patch_connect(protocol=stream)
        self.assertTrue(self.ip.pug.staged_players is None)
        self.loop.run_until_complete(self.b.start())
        self.loop.run_until_complete(self.b._read_handler)
        self.loop.run_until_complete(asyncio.Task(self.b.tasks.join(), loop=self.loop))
        self.assertFalse(self.ip.pug.staged_players is None)
        self.assertEquals(self.ip.pug.unstaged_players, {})

    def test_remove(self):
        stream = irc.parser.StreamProtocol(loop=self.loop)
        stream.feed_data(irc.messages.PrivMsg('#channel', ';add scout captain', prefix='nick!Nick@example.com').encode())

        transport, _ = self.patch_connect(protocol=stream)
        self.loop.run_until_complete(self.b.start())
        tests.utils.run_briefly(self.loop)
        self.loop.run_until_complete(asyncio.Task(self.b.tasks.join(), loop=self.loop))
        stream.feed_data(irc.messages.PrivMsg('#channel', ';remove', prefix='nick!Nick@example.com').encode())
        stream.feed_eof()
        self.loop.run_until_complete(self.b._read_handler)
        self.loop.run_until_complete(asyncio.Task(self.b.tasks.join(), loop=self.loop))
        self.assertEquals(len(self.ip.pug.unstaged_players), 0)

    def test_remove_non_existent(self):
        stream = irc.parser.StreamProtocol(loop=self.loop)
        stream.feed_data(irc.messages.PrivMsg('#channel', ';remove', prefix='nick!Nick@example.com').encode())
        stream.feed_eof()

        self.patch_connect(protocol=stream)
        self.loop.run_until_complete(self.b.start())
        self.loop.run_until_complete(self.b._read_handler)
        self.loop.run_until_complete(asyncio.Task(self.b.tasks.join(), loop=self.loop))
        self.assertEquals(len(self.ip.pug.unstaged_players), 0)

    def test_need_when_empty(self):
        pass

    def test_need_just_captains(self):
        pass

    def test_need_just_classes(self):
        pass

    def test_need_when_can_stage(self):
        pass

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