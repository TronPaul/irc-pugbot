import unittest
import unittest.mock
import irc_pugbot


CLASSES = ['scout', 'soldier', 'pyro', 'demoman', 'heavy', 'engineer', 'medic', 'sniper', 'spy']


class TestPugBot(unittest.TestCase):
    def test_add_any_class(self):
        for c in CLASSES:
            pb = irc_pugbot.Tf2Pug()
            pb.add('nick', [c])
            self.assertEquals(len(pb.unstaged_players), 1)
            self.assertEquals(pb.unstaged_players['nick'], ([c], False))

    def test_add_multi_class(self):
        for i in range(0, len(CLASSES)-1, 2):
            pb = irc_pugbot.Tf2Pug()
            pb.add('nick', [CLASSES[i], CLASSES[i+1]])
            self.assertEquals(len(pb.unstaged_players), 1)
            self.assertEquals(pb.unstaged_players['nick'], ([CLASSES[i], CLASSES[i+1]], False))

    def test_readd_different_class(self):
        pb = irc_pugbot.Tf2Pug()
        for c in CLASSES:
            pb.add('nick', [c])
            self.assertEquals(len(pb.unstaged_players), 1)
            self.assertEquals(pb.unstaged_players['nick'], ([c], False))

    def test_add_captain_with_class(self):
        for c in CLASSES:
            pb = irc_pugbot.Tf2Pug()
            pb.add('nick', [c], True)
            self.assertEquals(len(pb.unstaged_players), 1)
            self.assertEquals(pb.unstaged_players['nick'], ([c], True))

    def test_captain_fails_without_class(self):
        pb = irc_pugbot.Tf2Pug()
        self.assertRaises(irc_pugbot.MissingClassError, pb.add, 'nick', [], True)
        self.assertEquals(len(pb.unstaged_players), 0)

    def test_remove(self):
        pb = irc_pugbot.Tf2Pug()
        pb.add('nick', [CLASSES[0]])
        pb.remove('nick')
        self.assertEquals(len(pb.unstaged_players), 0)

    def test_remove_without_add_raises_error(self):
        pb = irc_pugbot.Tf2Pug()
        self.assertRaises(KeyError, pb.remove, 'nick')

    def test_simple_can_stage(self):
        pb = irc_pugbot.Tf2Pug()
        for i, c in enumerate(CLASSES):
            pb.add('nickA{0}'.format(i), [c], True)
            pb.add('nickB{0}'.format(i), [c], True)
        self.assertTrue(pb.can_stage)

    def test_cannot_stage_without_two_captains(self):
        pb = irc_pugbot.Tf2Pug()
        for i, c in enumerate(CLASSES):
            pb.add('nickA{0}'.format(i), [c])
            pb.add('nickB{0}'.format(i), [c])
        self.assertFalse(pb.can_stage)

    def test_cannot_stage_without_two_of_each_class(self):
        pb = irc_pugbot.Tf2Pug()
        for i in range(len(CLASSES)):
            pb.add('nickA{0}'.format(i), [CLASSES[0]])
            pb.add('nickB{0}'.format(i), [CLASSES[0]])
        self.assertFalse(pb.can_stage)

    def test_random_captains(self):
        captains = irc_pugbot.random_captains({'a': ([], True), 'b': ([], True), 'c': ([], True)})
        self.assertEquals(len(captains), 2)

    @unittest.mock.patch('irc_pugbot.random_captains')
    def test_stage(self, random_captains):
        pb = irc_pugbot.Tf2Pug()
        for i, c in enumerate(CLASSES):
            pb.add('nickA{0}'.format(i), [c], True)
            pb.add('nickB{0}'.format(i), [c], True)
        pb.stage()
        self.assertEquals(len(pb.unstaged_players), 0)
        self.assertEquals(len(pb.staged_players), 18)
