"""A documented NIL/roster-investment comparison; unknown is never zero."""
import json
from pathlib import Path

DEFAULT_PATH=Path(__file__).resolve().parents[1]/'data'/'nil_estimates.json'

def load(path=DEFAULT_PATH):
    path=Path(path)
    payload=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'teams':{}}
    return payload.get('teams',{})

def compare(away, home, teams):
    a=teams.get(away)
    h=teams.get(home)
    def acceptable(item):
        return bool(item and item.get('source_url') and item.get('as_of') and
                    item.get('metric') and isinstance(item.get('low_millions'),(float,int)) and
                    isinstance(item.get('high_millions'),(float,int)) and
                    0 <= item['low_millions'] <= item['high_millions'])
    a=a if acceptable(a) else None
    h=h if acceptable(h) else None
    result={'away':a,'home':h,'gap':None,'comparable':False}
    # Only compare values with same metric and as-of year, otherwise misleading.
    if a and h and a['metric']==h['metric'] and a['as_of'][:4]==h['as_of'][:4]:
        a_mid=(a['low_millions']+a['high_millions'])/2
        h_mid=(h['low_millions']+h['high_millions'])/2
        result.update(gap=round(a_mid-h_mid,2),comparable=True)
    return result
