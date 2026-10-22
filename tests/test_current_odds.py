from cfb.current_odds import normalize, match_game, parse_event, freshness


def test_tulane_and_memphis():
    assert normalize('Tulane Green Wave') == normalize('Tulane')
    assert normalize('Memphis Tigers') == normalize('Memphis')
    game = dict(id='123', home='Tulane Green Wave', away='Memphis Tigers', date='2026-10-16T23:00:00Z')
    event = dict(home_team='Tulane', away_team='Memphis', commence_time='2026-10-16T23:00:00Z')
    assert match_game(event, [game])['id'] == '123'


def test_ambiguous_rejected():
    x = dict(home_team='Tulane Green Wave', away_team='Memphis Tigers', commence_time='2026-10-16T23:00:00Z')
    g = dict(home='Tulane', away='Memphis', date='2026-10-16T23:00:00Z')
    assert match_game(x, [dict(g,id='1'),dict(g,id='2')]) is None


def test_spread_direction():
    e = dict(home_team='Tulane Green Wave', away_team='Memphis Tigers',bookmakers=[
        dict(title='Test', last_update='2026-10-16T15:00:00Z',markets=[
            dict(key='spreads',outcomes=[dict(name='Tulane Green Wave',point=6.5),dict(name='Memphis Tigers',point=-6.5)]),
            dict(key='totals',outcomes=[dict(name='Over',point=55.5)])])])
    result=parse_event(e,'2026-10-16T15:00:00Z')
    assert result['market_home_margin']==-6.5
    assert result['market_total']==55.5


def test_freshness():
    x={'collected_at':'2026-10-14T20:00:00Z'}
    assert freshness(x,'2026-10-16T19:00:00Z') == 'recent'
    assert freshness(x,'2026-10-16T21:00:00Z') == 'stale'


def test_missing():
    assert freshness({}) == 'unavailable'
