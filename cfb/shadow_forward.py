"""Immutable first-captured pregame Shadow research picks; never official Elo picks.

A four-hour assumed final-result delay is used in the shadow research replay.
Archived picks are actual captures, not reconstructed retroactive forecasts.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from .shadow_ratings import kickoff
from .time_safe import replay_shadow

DEFAULT_PATH = Path(__file__).resolve().parents[1] / 'data' / 'shadow_prediction_snapshots.jsonl'
FIELDS = ('id','season','week','date','home','away','home_id','away_id',
          'home_margin','home_win_prob','total','home_points','away_points','model_version')


def read_snapshots(path=DEFAULT_PATH):
    path=Path(path)
    if not path.exists(): return []
    rows=[]
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.strip(): rows.append(json.loads(line))
    return rows


def archive(games, path=DEFAULT_PATH, now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError('now must be timezone-aware')
    now=now.astimezone(timezone.utc)
    prior=read_snapshots(path)
    seen={(str(x['id']),x['model_version'],x['snapshot_utc'][:10]) for x in prior}
    new=[]
    for p in replay_shadow(games, as_of=now):
        if p.get('completed') or kickoff(p)<=now: continue
        key=(str(p['id']),p['model_version'],now.date().isoformat())
        if key in seen: continue
        row={field:p.get(field) for field in FIELDS}
        row.update(snapshot_utc=now.isoformat(),kind='shadow_research_pregame',
                   data_cutoff_utc=now.isoformat(),assumed_final_delay_hours=4)
        new.append(row)
        seen.add(key)
    if new:
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('a',encoding='utf-8') as handle:
            for row in new: handle.write(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n')
    return new


def first_pregame(games, path=DEFAULT_PATH):
    indexed={str(g['id']):g for g in games}
    first={}
    for p in sorted(read_snapshots(path),key=lambda p:p['snapshot_utc']):
        g=indexed.get(str(p['id']))
        if g is None or datetime.fromisoformat(p['snapshot_utc'])>=kickoff(g): continue
        first.setdefault(str(p['id']),p)
    return first


def forward_results(games,path=DEFAULT_PATH):
    first=first_pregame(games,path)
    indexed={str(g['id']):g for g in games}
    completed=[]
    for gid,p in first.items():
        g=indexed[gid]
        if not g.get('completed') or g.get('home_score') is None or g.get('away_score') is None:continue
        actual=float(g['home_score'])-float(g['away_score'])
        completed.append({'id':gid,'season':p['season'],'week':p['week'],
             'home':p['home'],'away':p['away'],'snapshot_utc':p['snapshot_utc'],
             'predicted_margin':p['home_margin'],'actual_margin':actual,
             'absolute_margin_error':abs(actual-float(p['home_margin'])),
             'winner_correct': None if actual==0 or float(p['home_margin'])==0 else (actual>0)==(float(p['home_margin'])>0),
             'predicted_total':p['total'],'actual_total':float(g['home_score'])+float(g['away_score'])})
    correct=[x['winner_correct'] for x in completed if x['winner_correct'] is not None]
    return {'archived_games':len(first),'graded_games':len(completed),
            'winner_accuracy':sum(correct)/len(correct) if correct else None,
            'margin_mae':sum(x['absolute_margin_error'] for x in completed)/len(completed) if completed else None,
            'rows':completed}
