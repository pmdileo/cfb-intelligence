from cfb.market_lines import normalize, find_espn_game, parse_lines


def test_normalize():
    assert normalize('LSU Tigers') == 'lsu'
    assert normalize('Oklahoma Sooners') == 'oklahoma'


def test_match():
    game = {'id': '123', 'home': 'LSU Tigers', 'away': 'Mississippi State Bulldogs', 'date': '2026-10-17T20:00:00Z'}
    event = {'homeTeam': 'LSU', 'awayTeam': 'Mississippi State', 'startDate': '2026-10-17T19:30:00Z'}
    assert find_espn_game(event, [game]) == game


def test_no_ambiguous_match():
    game = {'id': '123', 'home': 'LSU Tigers', 'away': 'Mississippi State Bulldogs', 'date': '2026-10-17T20:00:00Z'}
    event = {'homeTeam': 'LSU', 'awayTeam': 'Mississippi State', 'startDate': '2026-10-17T19:30:00Z'}
    assert find_espn_game(event, [game, game]) is None


def test_spread_sign_and_median():
    record = parse_lines({'lines': [
        {'provider': 'A', 'spread': -4.5, 'overUnder': 51},
        {'provider': 'B', 'spread': -3.5, 'overUnder': 52},
    ]})
    assert record['market_home_margin'] == 4.0
    assert record['market_total'] == 51.5


def test_missing():
    record = parse_lines({'lines': []})
    assert record['market_total'] is None
