from cfb.historical_markets import retrospective_grade, historical_rows

BASE = dict(id='1', season=2025, week=2, completed=True,
            home_score=24, away_score=21, home_margin=5.0, total=49.0)

def test_spread_and_total_grade():
    result = retrospective_grade(BASE, {'market_home_margin': 3.0, 'market_total': 47.0})
    assert result == {'su':'win', 'ats':'push', 'ou':'loss'}

def test_market_absent_is_not_loss():
    result = retrospective_grade(BASE, None)
    assert result['su']=='win' and result['ats']=='no_line' and result['ou']=='no_line'

def test_older_completed_game_scores_and_pending_excluded():
    future = {**BASE, 'id':'2', 'completed':False}
    rows=historical_rows([BASE, future], {'1':{'market_home_margin':3.0,'market_total':47.0}})
    assert len(rows)==1 and rows[0]['status']['ats']=='push'
    assert rows[0]['provenance']=='retrospective'

def test_does_not_mutate_forecast():
    initial=dict(BASE)
    retrospective_grade(BASE, {'market_home_margin': 4.0, 'market_total': 50.0})
    assert BASE==initial

def test_away_cover():
    pred={**BASE,'home_margin':-5.0,'home_score':14,'away_score':24,'total':45.0}
    result=retrospective_grade(pred, {'market_home_margin':-2.0,'market_total':48.0})
    assert result['su']=='win' and result['ats']=='win' and result['ou']=='win'
