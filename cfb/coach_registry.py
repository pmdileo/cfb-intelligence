"""Source-traceable coaching/roster research schema; not connected to predictions."""
from datetime import date

REQUIRED=('team_id','season','head_coach','source_url','verified_as_of')

def validate(entry):
    missing=[k for k in REQUIRED if not entry.get(k)]
    if missing: raise ValueError('Missing required fields: '+', '.join(missing))
    if not str(entry['season']).isdigit():raise ValueError('season must be a year')
    date.fromisoformat(entry['verified_as_of'])
    if not str(entry['source_url']).startswith(('https://','http://')):
        raise ValueError('source_url must be a URL')
    for metric in ('recruiting_score','returning_production_pct','coach_value_added'):
        if entry.get(metric) is not None and not isinstance(entry[metric],(int,float)):
            raise ValueError(metric+' must be numeric or null')
    return dict(entry)

def known_before(entries, kickoff_date):
    """No feature may be joined into a historic prediction if verified later."""
    cutoff=str(kickoff_date)[:10]
    return [validate(e) for e in entries if e.get('verified_as_of','9999-99-99')<=cutoff]
