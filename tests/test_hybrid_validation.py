from cfb.hybrid_validation import blend, score_pairs, validate_tournament, kickoff_overlap_audit
import pytest

def row(season,id,margin,total=45,actual_margin=3):
    return {'id':str(id),'season':season,'date':f'{season}-10-10T12:00:00Z',
      'home_id':'H','away_id':'A','completed':True,'home_score':24,'away_score':24-actual_margin,
      'home_margin':margin,'total':total}

def test_convex_endpoints():
    a=row(2021,1,-4);b=row(2021,1,5)
    assert blend(a,b,0)['home_margin']==-4
    assert blend(a,b,1)['home_margin']==5
    assert blend(a,b,.5)['home_margin']==.5

def test_reject_weight():
    with pytest.raises(ValueError):blend(row(2021,1,0),row(2021,1,0),1.1)

def test_training_season_only():
    base=[row(2021,1,-10),row(2022,2,-10),row(2023,3,-10),row(2024,4,3)]
    shadow=[row(2021,1,3),row(2022,2,3),row(2023,3,3),row(2024,4,-10)]
    results=validate_tournament(base,shadow,train_seasons=[2021,2022,2023],test_seasons=[2024])
    assert results['selected_shadow_weight']==1.0
    assert results['test_games']==1
    assert results['test_results'][0]['margin_mae'] < results['test_results'][1]['margin_mae']

def test_overlapping_splits_forbidden():
    with pytest.raises(ValueError):validate_tournament([],[],train_seasons=[2023],test_seasons=[2023])

def test_overlap_risk():
    x=[{'id':1,'date':'2025-09-01T12:00:00Z','completed':True,'home_score':10},
       {'id':2,'date':'2025-09-01T13:00:00Z','completed':False},
       {'id':3,'date':'2025-09-01T22:00:00Z','completed':False}]
    r=kickoff_overlap_audit(x)
    assert r['at_risk_games']==1 and r['overlap_pairs']==1

def test_empty_score():
    assert score_pairs([],0)['margin_mae'] is None
