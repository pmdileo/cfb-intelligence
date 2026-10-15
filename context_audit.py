"""Read-only optional audit: python context_audit.py --records path/to/data.csv"""
import argparse
import json
from cfb.context_features import load_records, coverage_report
from cfb.data import load_games

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--records', default='data/context_records.csv')
    args = p.parse_args()
    records = load_records(args.records)
    print(json.dumps({'records': len(records), 'coverage': coverage_report(records, load_games())}, indent=2))
