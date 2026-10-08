from cfb.data import parse_event

def test_parse_ranked_event():
    e={'id':'12','date':'2026-10-10T19:00Z','competitions':[{'competitors':[
       {'homeAway':'home','team':{'id':'1','displayName':'Alpha'},'curatedRank':{'current':3},'score':'42'},
       {'homeAway':'away','team':{'id':'2','displayName':'Beta'},'curatedRank':{'current':99},'score':'30'}],
       'status':{'type':{'completed':True}}}]}
    v=parse_event(e,2026,7)
    assert v['home_rank']==3 and v['away_rank'] is None and v['home_score']==42
