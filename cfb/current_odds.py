"""Optional timestamped current NCAA football odds, isolated from historical CFBD lines.

Home margin convention: positive = home favored. Do not rewrite historical lines.
"""
from __future__ import annotations
import json
import re
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / 'data' / 'current_odds.json'
URL = 'https://api.the-odds-api.com/v4/sports/americanfootball_ncaaf/odds/'
MASCOTS = ('green wave','blue raiders','red wolves','golden eagles','golden hurricane',
           'fighting irish','golden flashes','mean green','crimson tide','blue devils',
           'scarlet knights','yellow jackets','sun devils','running rebels',
           'wildcats','tigers','bulldogs','razorbacks','huskies','mustangs','cougars',
           'eagles','owls','rebels','bearcats','knights','aggies','longhorns',
           'warriors','pirates','hurricanes','panthers','volunteers','broncos',
           'falcons','spartans','trojans','wolverines','buckeyes','seminoles',
           'gators','cardinal','bears','ducks','cowboys','sooners','hawks','hawkeyes')
ALIASES = {'ole miss':'mississippi', 'miami fl':'miami', 'southern california':'usc',
           'southern cal':'usc', 'memphis':'memphis', 'tulane':'tulane'}


def utc(value):
    x = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    return x.replace(tzinfo=timezone.utc) if x.tzinfo is None else x.astimezone(timezone.utc)


def normalize(name):
    n = re.sub(r'[^a-z0-9 ]+', ' ', str(name or '').lower())
    n = re.sub(r'\s+', ' ', n).strip()
    for mascot in sorted(MASCOTS, key=len, reverse=True):
        if n.endswith(' ' + mascot):
            n = n[:-(len(mascot)+1)].strip()
            break
    return ALIASES.get(n, n)


def match_game(event, games, hours=18):
    """Require exact normalized teams + close kickoff; reject ambiguous matches."""
    home, away = normalize(event.get('home_team')), normalize(event.get('away_team'))
    if not home or not away or not event.get('commence_time'):
        return None
    kickoff = utc(event['commence_time'])
    candidates = [g for g in games if normalize(g.get('home')) == home and
                  normalize(g.get('away')) == away and g.get('date') and
                  abs((utc(g['date']) - kickoff).total_seconds()) <= 3600*hours]
    return candidates[0] if len(candidates) == 1 else None


def parse_event(event, received_at):
    """Extract bookmaker spreads and totals with source timestamps."""
    providers = {}
    for book in event.get('bookmakers') or []:
        name = book.get('title') or book.get('key')
        if not name:
            continue
        spread = total = None
        for market in book.get('markets') or []:
            if market.get('key') == 'spreads':
                for outcome in market.get('outcomes') or []:
                    if normalize(outcome.get('name')) == normalize(event.get('home_team')):
                        spread = outcome.get('point')
                        break
            elif market.get('key') == 'totals':
                for outcome in market.get('outcomes') or []:
                    if str(outcome.get('name','')).lower() == 'over':
                        total = outcome.get('point')
                        break
        try:
            spread = float(spread) if spread is not None else None
            total = float(total) if total is not None else None
        except (ValueError, TypeError):
            continue
        if spread is not None or total is not None:
            providers[name] = {'home_spread': spread, 'total': total,
                               'last_update': book.get('last_update') or received_at}
    margins = [-p['home_spread'] for p in providers.values() if p['home_spread'] is not None]
    totals = [p['total'] for p in providers.values() if p['total'] is not None]
    return {'market_home_margin': statistics.median(margins) if margins else None,
            'market_total': statistics.median(totals) if totals else None,
            'providers': providers, 'provider_count': len(providers),
            'collected_at': received_at, 'source': 'The Odds API',
            'line_timing': 'OBSERVED', 'commence_time': event.get('commence_time')}


def freshness(market, now=None, max_age_hours=48):
    if not market or not market.get('collected_at'):
        return 'unavailable'
    now = utc(now) if now else datetime.now(timezone.utc)
    try:
        age = (now - utc(market['collected_at'])).total_seconds()/3600
    except (ValueError, TypeError):
        return 'unavailable'
    if age < -0.1:
        return 'invalid'
    if age > max_age_hours:
        return 'stale'
    # A fresh API poll does not make an old bookmaker quote fresh.
    providers = market.get('providers') or {}
    seen = []
    for quote in providers.values():
        try:
            seen.append((now - utc(quote['last_update'])).total_seconds()/3600)
        except (KeyError, ValueError, TypeError):
            pass
    if seen and (min(seen) > max_age_hours or min(seen) < -0.1):
        return 'stale'
    return 'recent' 


def load(path=PATH):
    path = Path(path)
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def collect(games, api_key, *, path=PATH, session=None, now=None):
    """Fetch one current feed, preserve old observations but mark them stale in UI.

    No API key -> caller should skip invocation. Never fabricate an update.
    """
    if not api_key or not api_key.strip():
        raise ValueError('THE_ODDS_API_KEY missing')
    import requests
    session = session or requests.Session()
    now = utc(now) if now else datetime.now(timezone.utc)
    received = now.isoformat()
    response = session.get(URL, params={'apiKey': api_key.strip(), 'regions': 'us',
                                        'markets': 'spreads,totals', 'oddsFormat': 'american'}, timeout=45)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError('Unexpected current-odds API response')
    previous = load(path)
    updated = dict(previous)
    matched = unmatched = 0
    for event in payload:
        game = match_game(event, games)
        if not game:
            unmatched += 1
            continue
        parsed = parse_event(event, received)
        if parsed['provider_count']:
            updated[str(game['id'])] = parsed
            matched += 1
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(updated, indent=2, sort_keys=True), encoding='utf-8')
    temp.replace(path)
    return {'matched': matched, 'unmatched': unmatched, 'stored': len(updated),
            'collected_at': received}
