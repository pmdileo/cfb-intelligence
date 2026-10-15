from cfb.time_safe import replay_shadow,replay_baseline
import sys, types
try:
    import streamlit
except ImportError:
    sys.modules["streamlit"] = types.ModuleType("streamlit")
from cfb.shadow_research_ui import shadow_label

def g(i, hour, season=2025, home='H', away='A', completed=True, hs=50, aws=0):
    return dict(id=str(i),season=season,week=1,date=f'{season}-09-01T{hour:02}:00:00Z',
        home_id=home,away_id=away,home=home,away=away,completed=completed,
        home_score=hs if completed else None,away_score=aws if completed else None,neutral=True)

def test_overlap_does_not_know_result():
    games=[g(1,12),g(2,13),g(3,17)]
    for fn in (replay_shadow,replay_baseline):
        rows=fn(games)
        assert rows[0]['home_margin']==rows[1]['home_margin']
        assert rows[2]['home_margin'] != rows[0]['home_margin']

def test_simultaneous_protection():
    games=[g(1,12),g(2,12)]
    for fn in (replay_shadow,replay_baseline):
        rows=fn(games)
        assert rows[0]['home_margin']==rows[1]['home_margin']

def test_no_data_leakage_when_game_unfinished():
    games=[g(1,12,completed=False),g(2,17)]
    for fn in (replay_shadow,replay_baseline):
        rows=fn(games)
        assert rows[0]['home_margin']==rows[1]['home_margin']

def test_shadow_season_regresses_once():
    a=[g(1,12,season=2024),g(2,17,season=2024),g(3,12,season=2025),g(4,13,season=2025)]
    rows=replay_shadow(a)
    assert rows[2]['home_margin']==rows[3]['home_margin']

def test_cutoff_excludes_unavailable_results():
    a=[g(1,12),g(2,17)]
    for fn in (replay_shadow,replay_baseline):
        rows=fn(a,as_of='2025-09-01T14:00:00Z')
        assert rows[0]['home_margin']==rows[1]['home_margin']

def test_pick_label():
    assert shadow_label({'home':'Arkansas','away':'LSU'},{'home_margin':-5})=='LSU -5.0'
