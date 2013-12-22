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
        captains = irc_pugbot.random_captains({'a': ([], True), 'b': ([], True)})
        self.assertEquals(len(captains), 2)
        self.assertTrue('a' in captains)
        self.assertTrue('b' in captains)

    @unittest.mock.patch('irc_pugbot.random_captains')
    def test_stage(self, random_captains):
        pb = irc_pugbot.Tf2Pug()
        players = []
        for i, c in enumerate(CLASSES):
            player1 = ('nick0{0}'.format(i), [c])
            player2 = ('nick1{0}'.format(i), [c])
            players.append(player1)
            players.append(player2)
            pb.add(player1[0], player1[1], True)
            pb.add(player2[0], player2[1], True)
        print(pb.unstaged_players)
        captains = [players[0][0], players[1][0]]
        random_captains.return_value = captains
        pb.stage()
        self.assertFalse(captains[0] in pb.staged_players)
        self.assertFalse(captains[1] in pb.staged_players)
        self.assertEquals(pb.captains, captains)
        self.assertEquals(pb.teams[0], {})
        self.assertEquals(pb.teams[1], {})
        self.assertEquals(pb.picking_team, 0)

    def test_river(self):
        river = irc_pugbot.river()
        self.assertEquals(0, next(river))
        self.assertEquals(1, next(river))
        self.assertEquals(1, next(river))
        self.assertEquals(0, next(river))
        self.assertEquals(0, next(river))

    @unittest.mock.patch('irc_pugbot.random_captains')
    def test_simple_pick(self, random_captains):
        pb = irc_pugbot.Tf2Pug()
        players = []
        for i, c in enumerate(CLASSES):
            player1 = ('nick0{0}'.format(i), [c])
            player2 = ('nick1{0}'.format(i), [c])
            players.append(player1)
            players.append(player2)
            pb.add(player1[0], player1[1], True)
            pb.add(player2[0], player2[1], True)
        random_captains.return_value = [players[0][0], players[1][0]]
        pb.stage()
        pb.pick(players[2][0], 'scout')
        self.assertEquals(pb.teams[0], {'scout': players[2][0]})
        self.assertFalse(players[2][0] in pb.staged_players)
        self.assertEquals(pb.picking_team, 1)

    @unittest.mock.patch('irc_pugbot.random_captains')
    def test_cannot_pick_class_twice(self, random_captains):
        pb = irc_pugbot.Tf2Pug()
        players = []
        for i, c in enumerate(CLASSES):
            player1 = ('nick0{0}'.format(i), [c])
            player2 = ('nick1{0}'.format(i), [c])
            players.append(player1)
            players.append(player2)
            pb.add(player1[0], player1[1], True)
            pb.add(player2[0], player2[1], True)
        random_captains.return_value = [players[0][0], players[1][0]]
        pb.stage()
        pb.pick(players[2][0], 'scout')
        self.assertEquals(pb.teams[0], {'scout': players[2][0]})
        pb.pick(players[3][0], 'scout')
        self.assertRaises(irc_pugbot.ClassAlreadyPickedError, pb.pick, players[4][0], 'scout')

    def test_can_start_highlander(self):
        teams = [{CLASSES[j]: 'nick{0}{1}'.format(i, j) for j in range(8)} for i in range(2)]
        self.assertTrue(irc_pugbot.can_start_highlander(teams))

    @unittest.mock.patch('irc_pugbot.random_captains')
    def test_make_game(self, random_captains):
        pb = irc_pugbot.Tf2Pug()
        players = []

        def my_order():
            yield 0
            yield 1
            yield from irc_pugbot.river()

        order = my_order()
        for i, c in enumerate(CLASSES):
            player1 = ('nick{0}{1}'.format(next(order), i), [c])
            player2 = ('nick{0}{1}'.format(next(order), i), [c])
            players.append(player1)
            players.append(player2)
            pb.add(player1[0], player1[1], True)
            pb.add(player2[0], player2[1], True)
        random_captains.return_value = [players[0][0], players[1][0]]
        pb.stage()
        for (i, (nick, classes)) in enumerate(players[2:]):
            pb.pick(nick, classes[0])
        expected_teams = [{CLASSES[j]: 'nick{0}{1}'.format(i, j) for j in range(9)} for i in range(2)]
        teams = pb.make_game()
        self.assertEquals(teams, expected_teams)
        self.assertTrue(pb.captains is None)
        self.assertEquals(pb.staged_players, {})

    @unittest.mock.patch('irc_pugbot.random_captains')
    def test_make_game_moves_unpicked_to_unstanged(self, random_captains):
        pb = irc_pugbot.Tf2Pug()
        players = []

        def my_order():
            yield 0
            yield 1
            yield from irc_pugbot.river()

        order = my_order()
        for i, c in enumerate(CLASSES):
            player1 = ('nick{0}{1}'.format(next(order), i), [c])
            player2 = ('nick{0}{1}'.format(next(order), i), [c])
            players.append(player1)
            players.append(player2)
            pb.add(player1[0], player1[1], True)
            pb.add(player2[0], player2[1], True)
        pb.add('unpicked1', [CLASSES[1]])
        pb.add('unpicked2', [CLASSES[2]])
        random_captains.return_value = [players[0][0], players[1][0]]
        pb.stage()
        for (i, (nick, classes)) in enumerate(players[2:]):
            pb.pick(nick, classes[0])
        expected_teams = [{CLASSES[j]: 'nick{0}{1}'.format(i, j) for j in range(9)} for i in range(2)]
        teams = pb.make_game()
        self.assertEquals(teams, expected_teams)
        self.assertTrue(pb.captains is None)
        self.assertEquals(pb.staged_players, {})
        self.assertEquals(pb.unstaged_players, {'unpicked1': ([CLASSES[1]], False), 'unpicked2': ([CLASSES[2]], False)})