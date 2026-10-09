"""Create immutable pregame prediction snapshots after data collection."""
from cfb.data import load_games
from cfb.advanced import load_boxscores
from cfb.snapshots import snapshot_predictions

if __name__=='__main__':
    rows=snapshot_predictions(load_games(),boxscores=load_boxscores())
    print(f'Archived {len(rows)} new pregame snapshots')
