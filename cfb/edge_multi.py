"""Screen model-versus-market differences for user-selected forecast models.

This is a discrepancy screen, NOT a calibrated betting recommendation.
"""
from .current_odds import freshness, utc
from datetime import datetime, timezone


def scan_selected(forecasts, model_lookup, markets, *, season, week, models,
                  threshold=4.5, agreement='all', market_kind='Both', now=None):
    if not models:
        return []
    if agreement not in ('all', 'any'):
        raise ValueError('agreement must be all or any')
    if threshold < 0:
        raise ValueError('threshold cannot be negative')
    now = utc(now) if now else datetime.now(timezone.utc)
    output=[]
    for game in forecasts:
        if int(game['season']) != int(season) or int(game['week']) != int(week):
            continue
        if game.get('completed') or utc(game['date']) <= now:
            continue
        gid=str(game['id'])
        odds=markets.get(gid)
        if not odds or freshness(odds,now=now) != 'recent':
            continue
        if utc(odds['collected_at']) >= utc(game['date']):
            continue
        for label, line_key, projection_key in [('ATS','market_home_margin','home_margin'),('O/U','market_total','total')]:
            if market_kind not in ('Both', label):
                continue
            line=odds.get(line_key)
            if line is None:
                continue
            differences={}
            for model in models:
                record=model_lookup.get(model,{}).get(gid)
                if record is not None and record.get(projection_key) is not None:
                    differences[model]=float(record[projection_key])-float(line)
            if agreement == 'all':
                qualifies=len(differences)==len(models) and all(abs(v)>=threshold for v in differences.values()) and len({v>0 for v in differences.values()})==1
            else:
                qualifies=any(abs(v)>=threshold for v in differences.values())
            if not qualifies:
                continue
            primary=min(differences.values(),key=abs) if agreement=='all' else max(differences.values(),key=abs)
            side=(game['home'] if primary>0 else game['away']) if label=='ATS' else ('OVER' if primary>0 else 'UNDER')
            output.append({'id':gid,'kind':label,'side':side,'gap':round(abs(primary),2),
                           'differences':differences,'market_line':float(line),'game':game,
                           'agreement':len({v>0 for v in differences.values()})==1 and len(differences)==len(models),
                           'observed_at':odds['collected_at']})
    return sorted(output,key=lambda x:(-x['gap'],x['game']['date'],x['id']))
