from datetime import datetime,timezone,timedelta
from cfb.edge_scanner import classify_edge,scan_edges
NOW=datetime(2026,10,23,17,tzinfo=timezone.utc)
def fixture(e=10.5,s=11,total=60, shadow_total=61, market_margin=6,market_total=54):
    elo={"id":"1","home":"Home","away":"Away","date":"2026-10-25T18:00:00Z",
         "home_margin":e,"total":total,"completed":False}
    shadow={**elo,"home_margin":s,"total":shadow_total}
    market={"market_home_margin":market_margin,"market_total":market_total,
        "collected_at":"2026-10-23T16:00:00Z",
        "providers":{"Book":{"last_update":"2026-10-23T16:00:00Z"}},
        "provider_count":1}
    return elo,shadow,market
def test_agreed_ats_and_over():
    e,s,m=fixture()
    rows=classify_edge(e,s,m,now=NOW)
    assert len(rows)==2
    assert rows[0]["kind"]=="ATS" and rows[0]["side"]=="Home"
    assert rows[0]["edge_points"]==4.5
    assert rows[1]["side"]=="OVER"
def test_conflict_excluded_by_default():
    e,s,m=fixture(s=2,shadow_total=46)
    assert classify_edge(e,s,m,now=NOW)==[]
    rows=classify_edge(e,s,m,now=NOW,require_agreement=False)
    assert rows and any(not x["agreement"] for x in rows)
def test_stale_line_excluded():
    e,s,m=fixture()
    m["collected_at"]="2026-10-19T16:00:00Z"
    assert classify_edge(e,s,m,now=NOW)==[]
def test_after_kickoff_excluded():
    e,s,m=fixture()
    e["date"]="2026-10-22T18:00:00Z"
    assert classify_edge(e,s,m,now=NOW)==[]
def test_missing_totals_not_fabricated():
    e,s,m=fixture()
    m["market_total"]=None
    assert [x["kind"] for x in classify_edge(e,s,m,now=NOW)]==["ATS"]
def test_scan_scope():
    e,s,m=fixture()
    rows=scan_edges([e],{"1":s},{"1":m},now=NOW,kind="O/U")
    assert len(rows)==1 and rows[0]["kind"]=="O/U"
