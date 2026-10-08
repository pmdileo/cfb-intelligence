"""Optional ESPN game box-score refresh (can be run independently)."""
import argparse
from cfb.data import load_games
from cfb.advanced import collect_boxscores

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-new', type=int, default=100)
    args = parser.parse_args()
    report = collect_boxscores(load_games(), max_new=args.max_new)
    print(report)
    if report['errors'] and report['fetched'] == 0:
        print('Box-score feed currently unavailable; keeping existing cached statistics.')
