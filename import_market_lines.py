"""Run from repository root: python import_market_lines.py --start 2025 --end 2026"""
import argparse
import json
import os
from cfb.data import load_games
from cfb.market_lines import collect

parser = argparse.ArgumentParser()
parser.add_argument('--start', type=int, default=2025)
parser.add_argument('--end', type=int, default=2026)
args = parser.parse_args()
if args.start > args.end:
    parser.error('--start must be <= --end')
print(json.dumps(collect(range(args.start, args.end + 1), os.environ.get('CFBD_API_KEY'), load_games()), indent=2))
