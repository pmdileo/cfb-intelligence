from datetime import datetime
from cfb.forward_scoreboard import build_scoreboard


def game(id, completed=True):
    return {'id':str(id),'date':'2026-10-24T19:00:00Z','season':2026,'week':8,
            'home_id':'H','away_id':'A','home':'Home','away':'Away',
            'completed':completed,'home_score':31 if completed else None,
            'away_score':24 if completed else None}


def snap(id, margin, captured='2026-10-24T15:00:00Z', total=50, p=.6):
    return {'id':str(id),'snapshot_utc':captured,'home_id':'H','away_id':'A',
            'home_margin':margin,'total':total,'home_win_prob':p}


def test_paired_completed():
    r=build_scoreboard([game(1)],elo_snapshots=[snap(1,5)],shadow_snapshots=[snap(1,10)])
    assert r['graded_paired_games']==1
    assert r['overall']['elo']['winner_accuracy']==1
    assert r['overall']['shadow']['margin_mae']==3


def test_no_backfill_when_one_model_missing():
    r=build_scoreboard([game(1)],elo_snapshots=[snap(1,5)],shadow_snapshots=[])
    assert r['graded_paired_games']==0


def test_post_kickoff_rejected():
    r=build_scoreboard([game(1)],elo_snapshots=[snap(1,5,'2026-10-24T20:00:00Z')],shadow_snapshots=[snap(1,10)])
    assert r['graded_paired_games']==0


def test_first_capture_frozen():
    r=build_scoreboard([game(1)],elo_snapshots=[snap(1,5),snap(1,-5,'2026-10-24T17:00:00Z')],shadow_snapshots=[snap(1,10)])
    assert r['rows'][0]['elo_margin']==5


def test_completed_only():
    r=build_scoreboard([game(1,False)],elo_snapshots=[snap(1,5)],shadow_snapshots=[snap(1,10)])
    assert r['paired_pregame_games']==1 and r['graded_paired_games']==0


def test_team_identity_guard():
    altered=snap(1,5);altered['home_id']='OTHER'
    r=build_scoreboard([game(1)],elo_snapshots=[altered],shadow_snapshots=[snap(1,10)])
    assert r['graded_paired_games']==0


def test_disagreement_detection():
    r=build_scoreboard([game(1)],elo_snapshots=[snap(1,-2)],shadow_snapshots=[snap(1,10)])
    assert r['rows'][0]['models_disagree'] is True
