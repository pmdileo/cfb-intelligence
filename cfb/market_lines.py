"""CFBD historical lines ingestion with conservative ESPN game matching.

CFBD historical provider values are NOT guaranteed to be pregame snapshots;
never silently label them archival forward predictions.
"""
import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'data' / 'market_lines.json'
BASE = 'https://api.collegefootballdata.com/lines'


def normalize(name):
    name = str(name or '').casefold().replace('&', 'and')
    name = re.sub(r'[^a-z0-9]+', ' ', name)
    substitutions = {'st ': 'state ', 'univ ': 'university ', 'ucla ': 'ucla ',
                     'ole miss': 'mississippi', 'miami fl': 'miami', 'southern cal': 'usc'}
    for old, new in substitutions.items():
        if name == old.strip():
            name = new.strip()
    words = name.split()
    mascots = {'tigers','bulldogs','wildcats','crimson','tide','buckeyes','wolverines',
               'rebels','huskies','seminoles','gators','longhorns','aggies',
               'volunteers','razorbacks','cowboys','sooners','fighting','irish',
               'cougars','bruins','trojans','ducks','bears','golden','knights',
               'yellow','jackets','mountaineers','eagles','hawks','hawkeyes',
               'cardinals','redbirds','panthers','rams','red','wolves','spartans'}
    while words and words[-1] in mascots:
        words.pop()
    return ' '.join(words)


def iso_date(value):
    return datetime.fromisoformat(str(value).replace('Z', '+00:00')).date()


def find_espn_game(cfbd, espn_games):
    """Match same-day games with exact normalized home and away team names.

    Ambiguous games are skipped; no fuzzy or swapped-team match permitted.
    """
    result = []
    home = normalize(cfbd.get('homeTeam'))
    away = normalize(cfbd.get('awayTeam'))
    if not home or not away or not cfbd.get('startDate'):
        return None
    date = iso_date(cfbd['startDate'])
    for game in espn_games:
        if (normalize(game.get('home')) == home and normalize(game.get('away')) == away
                and iso_date(game['date']) == date):
            result.append(game)
    return result[0] if len(result) == 1 else None


def parse_lines(event):
    """CFBD spread is generally signed from home-team perspective.

    Spread -3.5 => home team favored 3.5; expected home margin +3.5.
    """
    by_provider = {}
    for line in event.get('lines') or []:
        provider = str(line.get('provider') or '').strip()
        spread = line.get('spread')
        total = line.get('overUnder')
        try:
            spread = float(spread) if spread is not None else None
            total = float(total) if total is not None else None
        except (ValueError, TypeError):
            continue
        if not provider or (spread is None and total is None):
            continue
        by_provider[provider] = {'home_spread': spread, 'total': total}
    margins = [-r['home_spread'] for r in by_provider.values() if r['home_spread'] is not None]
    totals = [r['total'] for r in by_provider.values() if r['total'] is not None]
    return {
        'market_home_margin': round(statistics.median(margins), 3) if margins else None,
        'market_total': round(statistics.median(totals), 3) if totals else None,
        'providers': by_provider,
        'provider_count': len(by_provider),
    }


def collect(years, api_key, games, path=PATH, session=None):
    """Download one season per request. A refresh may revise historical values.

    This is RESEARCH-ONLY historical context unless a timestamped line was
    explicitly captured in a genuine pregame snapshot.
    """
    if not api_key:
        raise ValueError('CFBD_API_KEY is required. Set it as a GitHub Actions secret.')
    session = session or requests.Session()
    path = Path(path)
    previous = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    results = dict(previous)
    report = {'matched': 0, 'unmatched': 0, 'seasons': []}
    for year in years:
        response = session.get(BASE, params={'year': int(year)},
                               headers={'Authorization': f'Bearer {api_key}'}, timeout=40)
        response.raise_for_status()
        events = response.json()
        if not isinstance(events, list):
            raise ValueError(f'Unexpected response for {year}')
        report['seasons'].append(int(year))
        for event in events:
            matched = find_espn_game(event, games)
            if not matched:
                report['unmatched'] += 1
                continue
            values = parse_lines(event)
            if values['provider_count'] == 0:
                continue
            results[str(matched['id'])] = {
                **values, 'espn_game_id': str(matched['id']),
                'cfbd_game_id': event.get('id'), 'season': int(year),
                'source': 'CollegeFootballData historical betting lines',
                'line_timing': 'UNVERIFIED',
            }
            report['matched'] += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding='utf-8')
    report['stored'] = len(results)
    return report


def load_lines(path=PATH):
    path = Path(path)
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
