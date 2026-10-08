from cfb.model import expected_home_margin, win_prob,build_predictions,evaluation

def fixture(id, date, hs=None, aws=None):
    return {'id':str(id),'date':date,'season':2025,'week':1,'home_id':'1','away_id':'2',
            'home':'Home','away':'Away','neutral':False,'completed':hs is not None,
            'home_score':hs,'away_score':aws}

def test_home_edge_and_win_probability():
    assert expected_home_margin(1500,1500,False)==2.5
    assert expected_home_margin(1500,1500,True)==0
    assert win_prob(2)>win_prob(-2)

def test_pregame_no_leakage():
    first=fixture(1,'2025-09-01T12:00:00Z',42,0)
    second=fixture(2,'2025-09-08T12:00:00Z')
    p=build_predictions([first,second])
    assert p[0]['home_elo']==1500
    assert p[1]['home_elo']>1500
    assert build_predictions([first,second],as_of='2025-08-30T12:00:00Z')[1]['home_elo']==1500

def test_report():
    g=build_predictions([fixture(1,'2025-09-01T12:00:00Z',28,20)])
    assert evaluation(g)['games']==1
