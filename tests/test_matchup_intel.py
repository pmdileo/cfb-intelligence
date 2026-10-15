from cfb.matchup_intel import abbreviated_team, matchup_insights, factors

def test_abbreviate():
    assert abbreviated_team('Mississippi State Bulldogs') == 'Bulldogs'
    assert abbreviated_team('LSU Tigers') == 'Tigers'

def test_quality_missing_is_not_fabricated():
    x=matchup_insights({'home':'A','away':'B','home_ypp_samples':0,'away_ypp_samples':0})
    assert x['ypp_usable'] is False
    assert 'Limited' in x['evidence']

def test_factors_keep_sign_and_zero():
    f=factors({'elo_contribution':-4.2,'venue_contribution':2.5})
    assert f[0]['points']==-4.2 and f[1]['points']==2.5
    assert f[-1]['points']==0

def test_metrics_favor_lower_allowed():
    d=matchup_insights({'home':'A','away':'B','home_allowed':14,'away_allowed':20,
                       'home_ppg':22,'away_ppg':30,'home_elo':1600,'away_elo':1500})
    m={x['metric']:x['leader'] for x in d['facts']}
    assert m['Recent points allowed/game']=='A'
    assert m['Recent points scored/game']=='B'
    assert m['Pregame Elo']=='A'
