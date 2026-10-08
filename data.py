"""Free scoreboard collector. ESPN endpoint is public but undocumented and may change."""
import datetime as dt
import json
import os
from pathlib import Path
import time
import requests

BASE='https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard'
DATA=Path(__file__).resolve().parents[1]/'data'

def fetch_week(year,week,session=None):
    session=session or requests.Session()
    response=session.get(BASE,params={'dates':year,'week':week,'seasontype':2,'groups':80,'limit':500},timeout=35,headers={'User-Agent':'CFBIntelligence/0.1'})
    response.raise_for_status()
    return response.json()

def parse_event(event,year,week):
    comps=event.get('competitions') or []
    if not comps: return None
    comp=comps[0]
    entries=comp.get('competitors') or []
    home=next((x for x in entries if x.get('homeAway')=='home'),None)
    away=next((x for x in entries if x.get('homeAway')=='away'),None)
    if not home or not away: return None
    def rank(entry):
        val=(entry.get('curatedRank') or {}).get('current')
        try:
            val=int(val)
            return val if 1<=val<=25 else None
        except (TypeError,ValueError): return None
    def score(entry):
        val=entry.get('score')
        if isinstance(val,dict): val=val.get('value',val.get('displayValue'))
        try: return int(float(val)) if val is not None else None
        except (TypeError,ValueError): return None
    status=(comp.get('status') or {}).get('type') or {}
    completed=bool(status.get('completed',False))
    h,a=home.get('team') or {},away.get('team') or {}
    return dict(id=str(event['id']),season=year,week=week,date=comp.get('date') or event.get('date'),
                home_id=str(h.get('id')),away_id=str(a.get('id')),home=h.get('displayName') or h.get('name'),
                away=a.get('displayName') or a.get('name'),home_rank=rank(home),away_rank=rank(away),
                home_score=score(home) if completed else None,away_score=score(away) if completed else None,
                completed=completed,status=status.get('name',''),neutral=bool(comp.get('neutralSite')),
                venue=(comp.get('venue') or {}).get('fullName',''),source='ESPN unofficial scoreboard',
                source_url=f"https://www.espn.com/college-football/game/_/gameId/{event['id']}")

def refresh(start=2021,end=None,pause=0.1):
    DATA.mkdir(exist_ok=True)
    now=dt.datetime.now(dt.timezone.utc)
    end=end or now.year
    path=DATA/'games.json'
    old={x['id']:x for x in json.loads(path.read_text())} if path.exists() else {}
    errors=[]; succeeded=0
    sess=requests.Session()
    for year in range(start,end+1):
        for week in range(1,17):
            if year==now.year and week>15 and now.month<11: continue
            try:
                batch=fetch_week(year,week,sess)
                for event in batch.get('events',[]):
                    obj=parse_event(event,year,week)
                    if obj: old[obj['id']]=obj
                succeeded+=1
            except Exception as exc:
                errors.append(f'{year} week {week}: {str(exc)[:180]}')
            time.sleep(pause)
    if not old: raise RuntimeError('No data retrieved; check ESPN feed access.')
    games=sorted(old.values(),key=lambda x:(x.get('date') or '',x['id']))
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(games,indent=2));os.replace(tmp,path)
    (DATA/'metadata.json').write_text(json.dumps(dict(refreshed_utc=now.isoformat(),weeks_succeeded=succeeded,week_errors=errors,
        game_count=len(games),source='ESPN unofficial public scoreboard',source_endpoint=BASE),indent=2))
    print(f'Refreshed {len(games)} games; successful weekly requests={succeeded}; errors={len(errors)}')
    if errors: print('\n'.join(errors[:8]))
    return games

def load_games():
    path=DATA/'games.json'
    return json.loads(path.read_text()) if path.exists() else []
