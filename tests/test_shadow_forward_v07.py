from datetime import datetime,timezone
from cfb.shadow_forward import archive,first_pregame,forward_results
from cfb.matchup_display_v07 import _side


def game(id,date,completed=False,home_score=None,away_score=None):
    return dict(id=str(id),season=2026,week=5,home_id='1',away_id='2',
        home='Miami Hurricanes',away='Tulane Green Wave',date=date,neutral=False,
        completed=completed,home_score=home_score,away_score=away_score)


def test_frozen_forward_first_pick(tmp_path):
    p=tmp_path/'snap.jsonl'
    g=[game(1,'2026-10-31T18:00:00Z')]
    assert len(archive(g,p,now=datetime(2026,10,30,12,tzinfo=timezone.utc)))==1
    assert len(archive(g,p,now=datetime(2026,10,30,13,tzinfo=timezone.utc)))==0
    assert len(first_pregame(g,p))==1
    finished=[game(1,'2026-10-31T18:00:00Z',True,31,20)]
    r=forward_results(finished,p)
    assert r['graded_games']==1 and r['margin_mae'] is not None


def test_never_backfill_after_kickoff(tmp_path):
    g=[game(2,'2026-10-31T18:00:00Z')]
    assert not archive(g,tmp_path/'a.jsonl',now=datetime(2026,10,31,19,tzinfo=timezone.utc))


def test_long_names_are_separate_from_spread():
    side,spread=_side(dict(home='Miami Hurricanes',away='North Carolina Tar Heels',home_margin=8.2))
    assert side=='Miami Hurricanes' and spread=='-8.2'
    assert _side(dict(home='A',away='B',home_margin=-2.5))==('B','-2.5')
    assert _side(dict(home='A',away='B',home_margin=0))==('Pick’em','PK')
