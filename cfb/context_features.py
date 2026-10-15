"""CFB Intelligence: time-aware context feature store (research only).

Never uses context not demonstrably available before prediction time.
All scores are source-supplied, not estimated or automatically weighted.
No updates to production predictions.
"""
from __future__ import annotations
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

NUMERIC_FIELDS = ('recruiting_score', 'transfer_net_score', 'returning_production_pct', 'coach_tenure_years', 'coach_value_added')
ALLOWED_TYPES = {'team_season', 'coach_change', 'game_context'}


def instant(value):
    if not value: raise ValueError('Every timestamp must be explicitly supplied')
    d = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if d.tzinfo is None: raise ValueError('Timestamp must contain timezone/UTC offset')
    return d.astimezone(timezone.utc)


def _optional_number(value, field):
    if value is None or value == '': return None
    try: n = float(value)
    except (ValueError, TypeError): raise ValueError(f'Invalid number for {field}')
    if not (-1e8 < n < 1e8): raise ValueError(f'Out of range {field}')
    if field == 'returning_production_pct' and not 0 <= n <= 100:
        raise ValueError('returning_production_pct must be 0..100')
    return n


def validate_record(row):
    """Require provenance, unambiguous identity and temporal publication evidence."""
    row = dict(row)
    required = ('record_id', 'type', 'team_id', 'season', 'known_at', 'source_url')
    for field in required:
        if not str(row.get(field) or '').strip(): raise ValueError(f'Missing {field}')
    if row['type'] not in ALLOWED_TYPES: raise ValueError('Unknown record type')
    if not str(row['source_url']).startswith(('https://', 'http://')): raise ValueError('source_url must be HTTP(S)')
    row['season'] = int(row['season'])
    row['known_at'] = instant(row['known_at']).isoformat()
    if row.get('effective_at'):
        row['effective_at'] = instant(row['effective_at']).isoformat()
    else:
        row['effective_at'] = row['known_at']
    for field in NUMERIC_FIELDS: row[field] = _optional_number(row.get(field), field)
    return row


def load_records(path):
    path = Path(path)
    if not path.exists(): return []
    if path.suffix.lower() == '.json':
        rows = json.loads(path.read_text(encoding='utf8'))
    elif path.suffix.lower() == '.csv':
        with path.open(newline='', encoding='utf8') as f: rows = list(csv.DictReader(f))
    else: raise ValueError('Only CSV and JSON are supported')
    if not isinstance(rows, list): raise ValueError('Expected a list of records')
    result = [validate_record(r) for r in rows]
    ids = [r['record_id'] for r in result]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate record_id')
    return result


def before_game(records, game, as_of=None):
    """Return only pre-existing context; explicit as_of must not be after kickoff."""
    kickoff = instant(game['date'])
    cutoff = instant(as_of) if as_of is not None else kickoff
    if cutoff > kickoff: raise ValueError('as_of cannot exceed kickoff for a pregame analysis')
    teams = {str(game['home_id']), str(game['away_id'])}
    season = int(game['season'])
    valid = [r for r in records
             if int(r['season']) == season and str(r['team_id']) in teams
             and instant(r['known_at']) < cutoff and instant(r['effective_at']) <= cutoff]
    return sorted(valid, key=lambda r: (r['known_at'], str(r['record_id'])))


def latest_features(records, game, as_of=None):
    """Latest documented values only; no future coaching/recruiting information."""
    chosen = {}
    for row in before_game(records, game, as_of):
        key = str(row['team_id'])
        if key not in chosen: chosen[key] = {'team_id': key, 'sources': [], 'head_coach': None, **{f: None for f in NUMERIC_FIELDS}}
        item = chosen[key]
        item['sources'].append({'record_id': row['record_id'], 'source_url': row['source_url'], 'known_at': row['known_at']})
        if row.get('head_coach'): item['head_coach'] = row['head_coach']
        for field in NUMERIC_FIELDS:
            if row[field] is not None: item[field] = row[field]
    return {team: chosen.get(team, {'team_id': team, 'sources': [], 'head_coach': None, **{f: None for f in NUMERIC_FIELDS}})
            for team in (str(game['home_id']), str(game['away_id']))}


def coverage_report(records, games):
    out = {'games': 0, 'games_with_any_context': 0, 'team_sides': 0, 'team_sides_with_context': 0,
           'missing_fields': {f: 0 for f in NUMERIC_FIELDS}}
    for g in games:
        out['games'] += 1
        features = latest_features(records, g)
        if any(v['sources'] for v in features.values()): out['games_with_any_context'] += 1
        for v in features.values():
            out['team_sides'] += 1
            if v['sources']: out['team_sides_with_context'] += 1
            for f in NUMERIC_FIELDS:
                if v[f] is None: out['missing_fields'][f] += 1
    return out
