"""Optional, independently cached ESPN box score information.

Endpoint is unofficial/undocumented; absence never becomes a zero.
"""
import json
import time
from pathlib import Path
import requests

SUMMARY_URL = 'https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary'
STATS_PATH = Path(__file__).resolve().parents[1] / 'data' / 'boxscores.json'


def number(value):
    try:
        if value is None or str(value).strip() in ('', '--', '-'):
            return None
        return float(str(value).replace(',', '').replace('%', ''))
    except (TypeError, ValueError):
        return None


def parse_boxscore(payload):
    """Returns {team_espn_id: normalized stats}; never guess missing stats."""
    result = {}
    teams = (payload.get('boxscore') or {}).get('players', [])
    # Only team aggregate statistics, never player rows.
    entries = (payload.get('boxscore') or {}).get('teams', [])
    for entry in entries:
        team = entry.get('team') or {}
        team_id = str(team.get('id') or '')
        if not team_id:
            continue
        raw = {}
        for statistic in entry.get('statistics') or []:
            keys = [str(statistic.get('name') or ''), str(statistic.get('label') or '')]
            for key in keys:
                if key:
                    raw[key.lower().replace(' ', '').replace('-', '')] = statistic.get('displayValue', statistic.get('value'))
        def get(*names):
            for name in names:
                value = number(raw.get(name.lower().replace(' ', '')))
                if value is not None:
                    return value
            return None
        total_yards = get('totalYards', 'totalyards')
        plays = get('totalOffensivePlays', 'totaloffensiveplays', 'totalplays')
        yards_per_play = get('yardsPerPlay', 'yardsperplay', 'yardsPerPlayAvg')
        if yards_per_play is None and total_yards is not None and plays and plays > 0:
            yards_per_play = total_yards / plays
        result[team_id] = {
            'total_yards': total_yards,
            'offensive_plays': plays,
            'yards_per_play': round(yards_per_play, 3) if yards_per_play is not None else None,
            'turnovers': get('turnovers'),
            'first_downs': get('firstDowns'),
        }
    return result


def collect_boxscores(games, max_new=125, pause=.1, session=None, path=STATS_PATH):
    """Fetch at most max_new uncached completed games per invocation.

    Does not overwrite already cached game summaries. Intended to run after
    the scoreboard refresh, and stay within a free GitHub Actions time budget.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(path.read_text()) if path.exists() else {}
    session = session or requests.Session()
    eligible = sorted((g for g in games if g.get('completed') and g.get('id') not in existing),
                      key=lambda g: g.get('date') or '', reverse=True)
    errors = []
    fetched = 0
    for game in eligible[:max_new]:
        try:
            response = session.get(SUMMARY_URL, params={'event': game['id']}, timeout=25,
                                   headers={'User-Agent': 'CFBIntelligence/0.3'})
            response.raise_for_status()
            stats = parse_boxscore(response.json())
            if not stats:
                raise ValueError('No team aggregates in response')
            existing[game['id']] = stats
            fetched += 1
        except (requests.RequestException, ValueError) as exc:
            errors.append(f"{game['id']}: {str(exc)[:100]}")
        time.sleep(max(0, pause))
    path.write_text(json.dumps(existing, indent=2, sort_keys=True))
    return dict(fetched=fetched, cached=len(existing), errors=errors,
                remaining=max(0, len(eligible)-max_new))


def load_boxscores(path=STATS_PATH):
    path = Path(path)
    return json.loads(path.read_text()) if path.exists() else {}
