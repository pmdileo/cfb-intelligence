"""Revisit missing-YPP game summaries, never overwrite complete stats with nulls."""
import argparse
import json
import time
from pathlib import Path
import requests
from cfb.advanced import SUMMARY_URL, STATS_PATH
from cfb.efficiency import team_metrics, repair_needed


def repair(max_games=100, pause=0.15, path=STATS_PATH, session=None):
    path = Path(path)
    if not path.exists():
        print('No cached boxscores to repair')
        return {'attempted': 0, 'improved_teams': 0, 'remaining': 0}
    data = json.loads(path.read_text(encoding='utf-8'))
    ids = [game_id for game_id, entries in data.items() if repair_needed(entries)]
    session = session or requests.Session()
    improved = 0
    attempts = 0
    failures = 0
    for game_id in ids[:max_games]:
        attempts += 1
        try:
            res = session.get(SUMMARY_URL, params={'event': game_id}, timeout=25,
                              headers={'User-Agent': 'CFBIntelligence/0.6'})
            res.raise_for_status()
            entries = (res.json().get('boxscore') or {}).get('teams') or []
            for entry in entries:
                team_id = str((entry.get('team') or {}).get('id') or '')
                if team_id not in data[game_id]:
                    continue
                calculated = team_metrics(entry.get('statistics'))
                previous = data[game_id][team_id]
                if previous.get('yards_per_play') is None and calculated['yards_per_play'] is not None:
                    for name in ('total_yards', 'offensive_plays', 'yards_per_play'):
                        if calculated[name] is not None:
                            previous[name] = calculated[name]
                    previous['play_count_source'] = calculated['play_count_source']
                    improved += 1
        except (requests.RequestException, ValueError, KeyError, TypeError):
            failures += 1
        time.sleep(max(0, pause))
    if improved:
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')
    result = {'attempted': attempts, 'improved_teams': improved,
              'failed_requests': failures, 'remaining_games': sum(repair_needed(v) for v in data.values())}
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-games', type=int, default=100)
    args = parser.parse_args()
    repair(max_games=args.max_games)
