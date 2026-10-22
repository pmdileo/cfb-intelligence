"""Read-only, matched, genuine pre-kickoff Elo versus Shadow comparison.

First archived pregame prediction per game is fixed independently for each model.
Metrics use only games whose final scores are recorded, and only games for which
both models have eligible snapshots. Never backfill missing forecasts.
No retrospective historical sportsbook prices are used to grade ATS/O-U.
"""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import json

ELO_PATH = Path(__file__).resolve().parents[1] / 'data' / 'prediction_snapshots.jsonl'
SHADOW_PATH = Path(__file__).resolve().parents[1] / 'data' / 'shadow_prediction_snapshots.jsonl'


def _utc(value):
    d = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('Snapshot and kickoff timestamps must include an offset')
    return d.astimezone(timezone.utc)


def _load(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def first_valid(rows, games):
    by_game = {str(g['id']): g for g in games}
    first = {}
    for p in sorted(rows, key=lambda row: row['snapshot_utc']):
        gid = str(p.get('id', ''))
        game = by_game.get(gid)
        if not game or not p.get('snapshot_utc') or not game.get('date'):
            continue
        try:
            if _utc(p['snapshot_utc']) >= _utc(game['date']):
                continue
        except (ValueError, TypeError):
            continue
        # Recorded schedule and participants must match the latest event, if present.
        if any(p.get(k) is not None and str(p[k]) != str(game[k])
               for k in ('home_id', 'away_id') if game.get(k) is not None):
            continue
        first.setdefault(gid, p)
    return first


def _model_metrics(rows, prefix):
    n = len(rows)
    if not n:
        return {'games': 0, 'winner_accuracy': None, 'decided_picks': 0,
                'margin_mae': None, 'total_mae': None, 'brier': None}
    decided = [r for r in rows if r['actual_margin'] != 0 and r[prefix+'_margin'] != 0]
    correct = sum((r[prefix+'_margin'] > 0) == (r['actual_margin'] > 0) for r in decided)
    return {
        'games': n,
        'winner_accuracy': correct / len(decided) if decided else None,
        'decided_picks': len(decided),
        'margin_mae': sum(abs(r[prefix+'_margin'] - r['actual_margin']) for r in rows) / n,
        'total_mae': sum(abs(r[prefix+'_total'] - r['actual_total']) for r in rows) / n,
        'brier': sum((r[prefix+'_prob'] - (1.0 if r['actual_margin'] > 0 else
                      0.0 if r['actual_margin'] < 0 else .5)) ** 2 for r in rows) / n,
    }


def build_scoreboard(games, elo_snapshots=None, shadow_snapshots=None,
                     elo_path=ELO_PATH, shadow_path=SHADOW_PATH):
    elo = first_valid(_load(elo_path) if elo_snapshots is None else elo_snapshots, games)
    shadow = first_valid(_load(shadow_path) if shadow_snapshots is None else shadow_snapshots, games)
    by_game = {str(g['id']): g for g in games}
    paired = set(elo) & set(shadow)
    rows = []
    completed = 0
    for gid in sorted(paired):
        g = by_game[gid]
        if not g.get('completed') or g.get('home_score') is None or g.get('away_score') is None:
            continue
        e, s = elo[gid], shadow[gid]
        try:
            am = float(g['home_score']) - float(g['away_score'])
            at = float(g['home_score']) + float(g['away_score'])
            ep, sp = float(e['home_win_prob']), float(s['home_win_prob'])
            em, sm = float(e['home_margin']), float(s['home_margin'])
            et, st = float(e['total']), float(s['total'])
        except (KeyError, TypeError, ValueError):
            continue
        if not 0 <= ep <= 1 or not 0 <= sp <= 1:
            continue
        completed += 1
        rows.append({
            'id': gid, 'season': int(g['season']), 'week': int(g.get('week') or 0),
            'matchup': f"{g.get('away','Away')} @ {g.get('home','Home')}",
            'kickoff': g['date'], 'elo_captured_at': e['snapshot_utc'],
            'shadow_captured_at': s['snapshot_utc'],
            'actual_margin': am, 'actual_total': at,
            'elo_margin': em, 'shadow_margin': sm,
            'elo_total': et, 'shadow_total': st,
            'elo_prob': ep, 'shadow_prob': sp,
            'elo_winner': 'home' if em > 0 else 'away' if em < 0 else 'pickem',
            'shadow_winner': 'home' if sm > 0 else 'away' if sm < 0 else 'pickem',
            'models_disagree': (em > 0 > sm) or (sm > 0 > em),
            'margin_disagreement': abs(em - sm),
        })
    rows.sort(key=lambda r: (r['season'], r['week'], r['kickoff'], r['id']))
    per_season = []
    for season in sorted({r['season'] for r in rows}):
        group = [r for r in rows if r['season'] == season]
        per_season.append({'season': season, 'games': len(group),
                           'elo': _model_metrics(group, 'elo'),
                           'shadow': _model_metrics(group, 'shadow')})
    return {'archived_elo_games': len(elo), 'archived_shadow_games': len(shadow),
            'paired_pregame_games': len(paired), 'graded_paired_games': completed,
            'overall': {'elo': _model_metrics(rows, 'elo'),
                        'shadow': _model_metrics(rows, 'shadow')},
            'by_season': per_season, 'rows': rows,
            'limitations': 'Only paired, first-captured before-kickoff snapshots are graded. '
                           'Historical unverified market lines are excluded. '
                           'Pregame capture alone does not prove each upstream input was timestamp-safe.'}
