from cfb.shadow_ratings import replay

def game(ident, date, home='1', away='2', hs=None, aws=None, season=2025):
    return dict(id=str(ident),date=date,season=season,home_id=home,away_id=away,
                neutral=False,completed=hs is not None,home_score=hs,away_score=aws)

def test_empty_and_initial_priors():
    assert replay([]) == []
    first=replay([game(1,'2025-09-01T12:00:00Z')])[0]
    assert abs(first['home_margin']-2.5)<1e-6

def test_future_result_never_affects_prior_prediction():
    earlier=game(1,'2025-09-01T12:00:00Z',hs=35,aws=10)
    future=game(2,'2025-09-08T12:00:00Z',hs=50,aws=0)
    a=replay([earlier,future])[0]
    b=replay([earlier,{**future,'home_score':0,'away_score':50}])[0]
    assert a['home_margin']==b['home_margin']

def test_prior_game_moves_later_prediction():
    a=game(1,'2025-09-01T12:00:00Z',hs=50,aws=0)
    b=game(2,'2025-09-08T12:00:00Z')
    assert replay([a,b])[1]['home_margin'] > 2.5

def test_cutoff_ignores_completed_future_results():
    a=game(1,'2025-09-01T12:00:00Z',hs=50,aws=0)
    b=game(2,'2025-09-08T12:00:00Z')
    rows=replay([a,b], as_of='2025-08-31T12:00:00Z')
    assert rows[1]['home_margin']==2.5

def test_same_kickoff_games_do_not_leak():
    a = game(1, '2025-09-01T12:00:00Z', hs=60, aws=0)
    b = game(2, '2025-09-01T12:00:00Z', hs=14, aws=14)
    assert replay([a, b])[1]['home_margin'] == 2.5
