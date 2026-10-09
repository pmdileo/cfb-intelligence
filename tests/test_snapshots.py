from datetime import datetime, timezone
from cfb.snapshots import snapshot_predictions, forward_report

def games():
    return [dict(id='a',season=2026,week=1,date='2026-10-10T20:00:00Z',home='Home',away='Away',
                 home_id='1',away_id='2',neutral=False,completed=False,home_score=None,away_score=None)]

def test_append_only(tmp_path):
    path=tmp_path/'archive.jsonl'
    now=datetime(2026,10,8,15,tzinfo=timezone.utc)
    a=snapshot_predictions(games(),archive_path=path,now=now)
    b=snapshot_predictions(games(),archive_path=path,now=now)
    assert len(a)==1 and b==[]
    assert len(path.read_text().splitlines())==1
    assert a[0]['kind']=='live_pregame'

def test_no_postkickoff_snapshot(tmp_path):
    rows=snapshot_predictions(games(),archive_path=tmp_path/'x.jsonl',now=datetime(2026,10,11,tzinfo=timezone.utc))
    assert rows==[]

def test_forward_report_uses_original_forecast(tmp_path):
    path=tmp_path/'archive.jsonl'
    snapshot_predictions(games(),archive_path=path,now=datetime(2026,10,8,tzinfo=timezone.utc))
    results=games()
    results[0].update(completed=True,home_score=28,away_score=14)
    report=forward_report(results,archive_path=path)
    assert report['summary']['games']==1
    assert report['rows'][0]['actual_home_margin']==14

def test_missing_archive(tmp_path):
    assert forward_report(games(),archive_path=tmp_path/'none')['summary']=={}
