import unittest
import irc_pugbot


CLASSES = ['scout', 'soldier', 'pyro', 'demoman', 'heavy', 'engineer', 'medic', 'sniper', 'spy']


class TestPugBot(unittest.TestCase):
    def test_add_any_class(self):
        for c in CLASSES:
            pb = irc_pugbot.Tf2Pug()
            pb.add('nick', [c])
            self.assertEquals(len(pb.unstaged_players), 1)
            self.assertEquals(pb.unstaged_players['nick'], [c])