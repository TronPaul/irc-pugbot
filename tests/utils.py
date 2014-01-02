import collections

CLASSES = ['scout', 'soldier', 'pyro', 'demoman', 'heavy', 'engineer', 'medic', 'sniper', 'spy']
TEAMS = ['RED', 'BLU']

Player = collections.namedtuple('Player', ['nick', 'classes'])


def generate_highlander_game():
    teams = []
    for team in TEAMS:
        teams.append(generate_highlander_team(team + '_'))
    return teams


def generate_highlander_team(prefix=''):
    players = []
    for i, cls in enumerate(CLASSES):
        players.append(Player('{0}player_{1}'.format(prefix, i), [cls]))
    return players