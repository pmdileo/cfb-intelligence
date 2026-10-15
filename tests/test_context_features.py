import csv
import tempfile
from pathlib import Path
import unittest
from cfb.context_features import validate_record, load_records, before_game, latest_features, coverage_report

GAME = dict(id='g', season=2026, date='2026-10-03T20:00:00Z', home_id='1', away_id='2')
BASE = dict(record_id='one', type='team_season', team_id='1', season=2026,
            known_at='2026-09-01T00:00:00Z', source_url='https://example.org/1', recruiting_score='80')

class Tests(unittest.TestCase):
    def test_first_known_record(self):
        x = latest_features([validate_record(BASE)], GAME)
        self.assertEqual(x['1']['recruiting_score'], 80)
        self.assertIsNone(x['2']['recruiting_score'])
    def test_future_information_leakage(self):
        future = validate_record({**BASE, 'record_id': 'new', 'known_at': '2026-10-05T00:00:00Z', 'recruiting_score': '99'})
        self.assertEqual(len(before_game([future], GAME)), 0)
    def test_no_post_kickoff_asof(self):
        with self.assertRaises(ValueError): latest_features([], GAME, as_of='2026-10-04T00:00:00Z')
    def test_effective_date(self):
        future = validate_record({**BASE, 'effective_at': '2026-11-01T00:00:00Z'})
        self.assertEqual(before_game([future], GAME), [])
    def test_latest_doesnt_erase_known_values(self):
        old = validate_record(BASE)
        new = validate_record({**BASE, 'record_id': 'two', 'known_at': '2026-09-10T00:00:00Z', 'head_coach': 'Coach B', 'recruiting_score': ''})
        f = latest_features([new, old], GAME)['1']
        self.assertEqual(f['recruiting_score'], 80)
        self.assertEqual(f['head_coach'], 'Coach B')
    def test_reject_ambiguous_timestamps_and_urls(self):
        with self.assertRaises(ValueError): validate_record({**BASE, 'known_at': '2026-09-01'})
        with self.assertRaises(ValueError): validate_record({**BASE, 'source_url': 'citation-needed'})
    def test_reject_invalid_production(self):
        with self.assertRaises(ValueError): validate_record({**BASE, 'returning_production_pct': '140'})
    def test_csv_loader(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'records.csv'
            with p.open('w',newline='') as f:
                w = csv.DictWriter(f, fieldnames=list(BASE));w.writeheader();w.writerow(BASE)
            self.assertEqual(len(load_records(p)), 1)
    def test_coverage_count(self):
        o = coverage_report([validate_record(BASE)], [GAME]);self.assertEqual((o['games_with_any_context'],o['team_sides_with_context']), (1,1))

if __name__ == '__main__': unittest.main()
