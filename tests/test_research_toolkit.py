import pytest
from cfb.research_audit import inspect_boxscores, market_coverage
from cfb.forecast_validation import evaluate_rows, compare_same_games, archived_live_rows
from cfb.coach_registry import validate, known_before

G={'id':'1','home_id':'a','away_id':'b','date':'2026-10-14T20:00Z','season':2026,'week':7,'completed':True,'home_score':21,'away_score':17,'home_margin':3.0,'total':40,'home_win_prob':.65}

def test_scorecard():
    r=evaluate_rows([G]);assert r['games']==1 and r['winner_accuracy']==1 and r['margin_mae']==1

def test_paired_rejects_inconsistent_game():
    with pytest.raises(ValueError):compare_same_games([G],[{**G,'home_score':99}])

def test_compare_pairs():
    r=compare_same_games([G], [{**G,'home_margin':1}],minimum_games=1)
    assert r['paired_games']==1 and r['enough_games']

def test_boxscore_audit():
    r=inspect_boxscores({'1':{'a':{'total_yards':420,'offensive_plays':70,'yards_per_play':6.0}}})
    assert r['yards_per_play_available']==1 and r.get('ypp_inconsistent',0)==0

def test_coverage():
    assert market_coverage([G],{'1':{'market_home_margin':2,'market_total':43}})['2026']['spreads']==1

def test_snapshot_cutoff():
    snaps=[{**G,'snapshot_utc':'2026-10-14T18:00Z'}, {**G,'snapshot_utc':'2026-10-14T22:00Z'}]
    rows=archived_live_rows(snaps,[G]);assert len(rows)==1 and rows[0]['snapshot_utc']=='2026-10-14T18:00Z'

def test_coach_source_and_cutoff():
    c={'team_id':'1','season':2026,'head_coach':'Example','source_url':'https://example.edu','verified_as_of':'2026-10-13'}
    assert validate(c)['head_coach']=='Example'
    assert len(known_before([c],'2026-10-14T18:00Z'))==1
    assert known_before([c],'2026-10-12')==[]
