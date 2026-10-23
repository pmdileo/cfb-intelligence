"""Model-vs-market discrepancy scanner. Screening, not betting confidence."""
from datetime import datetime, timezone
from .current_odds import freshness, utc

def classify_edge(elo, shadow, market, *, now=None, min_edge=4.5, require_agreement=True):
    now = utc(now) if now else datetime.now(timezone.utc)
    if not market or freshness(market, now=now) != "recent":
        return []
    if utc(elo["date"]) <= now or utc(market["collected_at"]) >= utc(elo["date"]) or elo.get("completed"):
        return []
    if str(elo.get("id")) != str(shadow.get("id")):
        return []
    if min_edge < 0:
        raise ValueError("min_edge cannot be negative")
    result = []
    for kind, line, key in (("ATS", market.get("market_home_margin"), "home_margin"),
                            ("O/U", market.get("market_total"), "total")):
        if line is None or elo.get(key) is None or shadow.get(key) is None:
            continue
        e, s = float(elo[key])-float(line), float(shadow[key])-float(line)
        agree = e*s > 0
        strength = min(abs(e),abs(s)) if require_agreement else max(abs(e),abs(s))
        if strength < min_edge or (require_agreement and not agree):
            continue
        direction = e if require_agreement or abs(e)>=abs(s) else s
        side = (elo["home"] if direction>0 else elo["away"]) if kind=="ATS" else ("OVER" if direction>0 else "UNDER")
        result.append({"id":str(elo["id"]),"kind":kind,"side":side,
          "elo_edge":round(e,2),"shadow_edge":round(s,2),"market_line":float(line),
          "elo_projection":float(elo[key]),"shadow_projection":float(shadow[key]),
          "agreement":agree,"edge_points":round(strength,2),
          "home":elo["home"],"away":elo["away"],"kickoff":elo["date"],
          "observed_at":market["collected_at"],"provider_count":market.get("provider_count",0)})
    return result

def scan_edges(forecasts, shadow_by_id, odds_by_id, *, now=None, min_edge=4.5, require_agreement=True, kind="Both"):
    found=[]
    for elo in forecasts:
        gid=str(elo.get("id"))
        shadow=shadow_by_id.get(gid)
        if shadow:
            found.extend(x for x in classify_edge(elo,shadow,odds_by_id.get(gid),now=now,
                min_edge=min_edge,require_agreement=require_agreement) if kind=="Both" or x["kind"]==kind)
    return sorted(found,key=lambda x:(-x["edge_points"],x["kickoff"],x["id"]))
