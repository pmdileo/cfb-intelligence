"""Archive official Elo forecasts; report selection counts for troubleshooting.

Only saves real before-kickoff forecasts. Does not backfill or change the model.
"""
from collections import Counter
from datetime import datetime, timezone
from cfb.data import load_games
from cfb.advanced import load_boxscores
from cfb.model import build_predictions, timestamp
from cfb.snapshots import snapshot_predictions, _read, DEFAULT_PATH

if __name__ == '__main__':
    now = datetime.now(timezone.utc)
    games = load_games()
    boxscores = load_boxscores()
    predictions = build_predictions(games, as_of=now, boxscores=boxscores)
    upcoming = [p for p in predictions if timestamp(p.get('date')) > now]
    eligible = [p for p in upcoming if not p.get('completed')]
    previous = _read(DEFAULT_PATH)
    print(f'ELO DIAGNOSTICS: games={len(games)}, forecasts={len(predictions)}, '
          f'kickoff_in_future={len(upcoming)}, eligible_uncompleted={len(eligible)}, '
          f'existing_archive={len(previous)}', flush=True)
    print('ELO DIAGNOSTICS future completed flags: '
          + repr(dict(Counter(str(bool(p.get('completed'))) for p in upcoming))), flush=True)
    print('ELO DIAGNOSTICS examples: '
          + repr([(p.get('id'), p.get('date'), p.get('completed')) for p in upcoming[:5]]), flush=True)
    additions = snapshot_predictions(games, boxscores=boxscores, now=now)
    print(f'Archived {len(additions)} new pregame snapshots', flush=True)
    if eligible and not previous and not additions:
        raise RuntimeError('Elo has eligible future games but saved zero snapshots. Investigate archive writer.')
