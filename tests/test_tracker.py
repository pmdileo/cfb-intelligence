from datetime import datetime,timezone
from cfb.tracker import grade_game, record, tracker_rows
from cfb.snapshots import snapshot_predictions

G={'id':'a','home_id':'1','away_id':'2','home':'Home','away':'Away','season':2026,'week':7,'date':'2026-10-11T20:00:00Z','completed':False,'home_score':None,'away_score':None}

def test_grading_three_independent_results():
    p={'home_margin':7.0,'total':54,'market_home_margin':3.5,'market_total':50.5}
    g={'completed':True,'home_score':28,'away_score':24}
    assert grade_game(p,g)=={'su':'win','ats':'win','ou':'win'}
    p['market_home_margin']=6.5
    assert grade_game(p,g)['ats']=='loss'
    p['market_total']=52
    assert grade_game(p,g)['ou']=='push'

def test_no_line_is_not_loss():
    assert grade_game({'home_margin':5,'total':45},{'completed':True,'home_score':26,'away_score':21})=={'su':'win','ats':'no_line','ou':'no_line'}

def test_archive_genuine_only(tmp_path):
    path=tmp_path/'predictions.jsonl'
    when=datetime(2026,10,11,12,tzinfo=timezone.utc)
    result=snapshot_predictions([G],archive_path=path,now=when)
    assert len(result)==1
    assert len(snapshot_predictions([G],archive_path=path,now=when))==0
    game={**G,'completed':True,'home_score':30,'away_score':20}
    rows=tracker_rows([game],path)
    assert len(rows)==1 and rows[0]['status']['su']=='win'
    assert record(rows,'ats')['losses']==0
