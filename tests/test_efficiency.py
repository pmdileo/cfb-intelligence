from cfb.efficiency import team_metrics, repair_needed


def s(name, value):
    return {'name': name, 'displayValue': value}


def test_calculate_from_attempts():
    r = team_metrics([s('totalYards', '420'), s('rushingAttempts', '35'), s('passingAttempts', '25')])
    assert r['offensive_plays'] == 60
    assert r['yards_per_play'] == 7
    assert r['play_count_source'] == 'derived_rush_plus_pass'


def test_parse_completion_attempts():
    r = team_metrics([s('totalYards', '300'), s('rushingAttempts', '30'), s('completionAttempts', '18/30')])
    assert r['offensive_plays'] == 60
    assert r['yards_per_play'] == 5


def test_never_guess_if_missing():
    r = team_metrics([s('totalYards', '450'), s('rushingAttempts', '29')])
    assert r['yards_per_play'] is None
    assert r['offensive_plays'] is None


def test_reported_plays_preferred():
    r = team_metrics([s('totalYards', '400'), s('totalOffensivePlays', '50'), s('rushingAttempts','40'),s('passingAttempts','20')])
    assert r['offensive_plays'] == 50
    assert r['yards_per_play'] == 8


def test_repair_needed():
    assert repair_needed({'1': {'yards_per_play': None}})
    assert not repair_needed({'1': {'yards_per_play': 6.2}})
