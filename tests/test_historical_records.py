# The result calculation does not use Streamlit; stub it for lean test environments.
import sys
import types
try:
    import streamlit
except ImportError:
    sys.modules['streamlit'] = types.ModuleType('streamlit')
from cfb.tracker_ui import retrospective_rows
from cfb.tracker import record

def test_historical_winner_record():
    games=[
        dict(id='1',season=2026,week=6,completed=True,home_margin=3,home_score=21,away_score=17,total=44),
        dict(id='2',season=2026,week=6,completed=True,home_margin=2,home_score=14,away_score=24,total=40),
        dict(id='3',season=2026,week=7,completed=False,home_margin=5,home_score=None,away_score=None,total=55),
    ]
    rows=retrospective_rows(games)
    assert len(rows)==2
    assert record(rows,'su')['wins']==1
    assert record(rows,'su')['losses']==1
    assert record(rows,'ats')['no_line']==2
    assert record(rows,'ou')['no_line']==2
    assert all(r['provenance']=='retrospective' for r in rows)

def test_only_selected_week_counted():
    games=[dict(id=str(i),season=2026,week=wk,completed=True,home_margin=2,home_score=21,away_score=14,total=40) for i,wk in enumerate([6,6,7])]
    rows=retrospective_rows(games)
    weekly=[r for r in rows if r['week']==6]
    assert record(weekly,'su')['wins']==2
    assert record(rows,'su')['wins']==3
