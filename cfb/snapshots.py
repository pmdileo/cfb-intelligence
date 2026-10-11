"""Append-only pregame forecast snapshots and real-time evaluation.

No backfilling: snapshots are only created for games whose kickoff is in the future.
Chronological replay is kept separate from genuine live predictions.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from .model import build_predictions, timestamp, evaluation

DEFAULT_PATH = Path(__file__).resolve().parents[1] / 'data' / 'prediction_snapshots.jsonl'
PREDICTION_FIELDS = ('id','season','week','date','home','away','home_id','away_id','home_margin','home_win_prob','total','home_points','away_points','model_version')


def _read(path):
    path=Path(path)
    if not path.exists(): return []
    rows=[]
    for i,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        try: rows.append(json.loads(line))
        except json.JSONDecodeError as e: raise ValueError(f'Invalid archive JSON on line {i}') from e
    return rows


def snapshot_predictions(games,boxscores=None,archive_path=DEFAULT_PATH,now=None):
    """Save a versioned immutable prediction per game/run; return newly archived entries.

    Same game and model version are not overwritten during a single UTC day.
    Subsequent updates on a new date become separate revisions. Only predictions
    created before kickoff qualify for genuine forward-performance measurement.
    """
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError('now must be timezone aware')
    now=now.astimezone(timezone.utc)
    cutoff=now.isoformat()
    # Don't replay results newer than now; historical outcomes are only used
    # if the game's kickoff predates now. This does not know finalization time,
    # so only run this after upstream scoreboard has refreshed accurately.
    forecasts=build_predictions(games,as_of=now,boxscores=boxscores or {})
    archive_path=Path(archive_path)
    previous=_read(archive_path)
    existing={(str(x['id']),x['model_version'],x['snapshot_utc'][:10]) for x in previous}
    additions=[]
    for p in forecasts:
        kickoff=timestamp(p['date'])
        if kickoff<=now or p.get('completed'): continue
        key=(str(p['id']),p['model_version'],now.date().isoformat())
        if key in existing: continue
        item={k:p.get(k) for k in PREDICTION_FIELDS}
        item.update(snapshot_utc=cutoff,kind='live_pregame',data_cutoff_utc=cutoff)
        additions.append(item)
        existing.add(key)
    if additions:
        archive_path.parent.mkdir(parents=True,exist_ok=True)
        with archive_path.open('a',encoding='utf-8') as f:
            for row in additions: f.write(json.dumps(row,separators=(',',':'),sort_keys=True)+'\n')
    return additions


def forward_report(games,archive_path=DEFAULT_PATH):
    """Score first archived pregame forecast of each game against official final.

    Does not recompute or overwrite archived predictions. Returns summary + rows.
    """
    by_id={str(g['id']):g for g in games}
    first={}
    for p in sorted(_read(archive_path),key=lambda x:x['snapshot_utc']):
        g=by_id.get(str(p['id']))
        if not g: continue
        if timestamp(p['snapshot_utc'])>=timestamp(g['date']):continue
        first.setdefault(str(p['id']),p)
    evaluated=[]
    for gid,p in first.items():
        g=by_id[gid]
        if not g.get('completed') or g.get('home_score') is None or g.get('away_score') is None:continue
        evaluated.append({**p,'completed':True,'home_score':g['home_score'],'away_score':g['away_score'],
                          'actual_home_margin':g['home_score']-g['away_score'],
                          'actual_total':g['home_score']+g['away_score']})
    return {'summary':evaluation(evaluated),'rows':evaluated,'archived_games':len(first)}
