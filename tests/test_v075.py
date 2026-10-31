from datetime import datetime,timezone
from cfb.nil_comparison import compare
from cfb.edge_multi import scan_selected
NOW=datetime(2026,10,30,17,tzinfo=timezone.utc)
def test_nil_unknown_never_zero():
    r=compare('A','B',{})
    assert r['gap'] is None and not r['comparable']
def test_nil_comparable_only():
    a={'low_millions':10,'high_millions':12,'source_url':'https://example.org/a','as_of':'2026-09-01','metric':'roster value'}
    b={**a,'low_millions':2,'high_millions':4}
    assert compare('A','B',{'A':a,'B':b})['gap']==8
    b['metric']='revenue share'
    assert compare('A','B',{'A':a,'B':b})['gap'] is None
def fixture():
    g={'id':'1','season':2026,'week':9,'date':'2026-11-01T17:00:00Z','home':'H','away':'A','completed':False,'home_margin':10.5,'total':61}
    shadow={**g,'home_margin':11.2,'total':62}
    odds={'collected_at':'2026-10-30T16:00:00Z','market_home_margin':6,'market_total':55,'providers':{'Book':{'last_update':'2026-10-30T16:00:00Z'}}}
    return g,shadow,odds
def test_week_isolation_and_model_choice():
    g,s,o=fixture()
    args=dict(forecasts=[g],model_lookup={'Elo':{'1':g},'Shadow':{'1':s}},markets={'1':o},season=2026,models=['Elo','Shadow'],now=NOW)
    assert not scan_selected(**args,week=8)
    found=scan_selected(**args,week=9)
    assert {x['kind'] for x in found}=={'ATS','O/U'}
    assert scan_selected(**{**args,'models':['Elo']},week=9)
def test_all_requires_every_selected_model():
    g,s,o=fixture()
    s['home_margin']=2
    r=scan_selected([g],{'Elo':{'1':g},'Shadow':{'1':s}}, {'1':o},season=2026,week=9,models=['Elo','Shadow'],market_kind='ATS',now=NOW)
    assert not r
    r=scan_selected([g],{'Elo':{'1':g},'Shadow':{'1':s}}, {'1':o},season=2026,week=9,models=['Elo','Shadow'],market_kind='ATS',agreement='any',now=NOW)
    assert len(r)==1
