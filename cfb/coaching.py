"""Conservative coaching-data schema. No invented coach ratings.

Coaching effects will be estimated only after verified season/team records are loaded
and controlled for opponent strength, previous team ability and roster talent.
"""
import csv
from pathlib import Path

REQUIRED=('season','team_id','team_name','head_coach','source_url','verified_on')
OPTIONAL=('first_year','coordinator','prior_coach','recruiting_rank','transfer_rank','returning_production_pct','notes')
FIELDS=REQUIRED+OPTIONAL

def load_coaches(path):
    path=Path(path)
    if not path.exists():return []
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        missing=set(REQUIRED)-set(reader.fieldnames or [])
        if missing: raise ValueError(f'Missing columns: {sorted(missing)}')
        rows=list(reader)
    for i,r in enumerate(rows,2):
        if any(not r.get(k,'').strip() for k in REQUIRED):raise ValueError(f'Unverified/missing required value at line {i}')
        if not str(r['season']).isdigit():raise ValueError(f'Invalid season at line {i}')
    return rows
