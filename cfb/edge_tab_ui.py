"""Dedicated EDGE view with conservative model agreement screening."""
import pandas as pd
import streamlit as st
from .edge_scanner import scan_edges

def render_edge_tab(forecasts, shadow_by_id, current_odds, now):
    st.subheader("EDGE · Model vs sportsbook")
    st.caption("A model–market discrepancy is NOT a validated betting advantage or profit probability.")
    a,b,c=st.columns([1.2,1,1.4])
    threshold=a.slider("Minimum edge (points)",0.5,15.0,4.5,0.5,key="edge_threshold")
    kind=b.selectbox("Market",["Both","ATS","O/U"],key="edge_market")
    require=c.selectbox("Filter",["Both models agree","Either model (research)"],key="edge_agreement")=="Both models agree"
    rows=scan_edges(forecasts,shadow_by_id,current_odds,now=now,min_edge=threshold,require_agreement=require,kind=kind)
    st.metric("Qualified discrepancies",len(rows))
    st.caption("ATS edge = projected home margin minus market home margin; O/U edge = projected total minus market total. Positive = home ATS / Over; negative = away ATS / Under.")
    if not rows:
        st.info("No matchups with qualifying recent odds. Try a lower threshold or refresh sportsbook observations.")
        return
    table=[{"Matchup":f'{x["away"]} @ {x["home"]}',"Market":x["kind"],"Side":x["side"],
        "Edge points":x["edge_points"],"Elo vs market":x["elo_edge"],"Shadow vs market":x["shadow_edge"],
        "Consensus":x["market_line"],"Kickoff UTC":x["kickoff"]} for x in rows]
    st.dataframe(pd.DataFrame(table),hide_index=True,use_container_width=True)
    for x in rows:
        with st.expander(f'{x["kind"]} · {x["away"]} @ {x["home"]} · {x["side"]} · {x["edge_points"]:.1f} points'):
            st.write(f'Sportsbook consensus: **{x["market_line"]:.1f}** · Elo projection: **{x["elo_projection"]:.1f}** · Shadow projection: **{x["shadow_projection"]:.1f}**')
            st.write(f'Elo edge: **{x["elo_edge"]:+.1f}** · Shadow edge: **{x["shadow_edge"]:+.1f}**')
            st.caption(f'{x["provider_count"]} providers · Observed {x["observed_at"]} · Kickoff {x["kickoff"]}')
            if not x["agreement"]:
                st.warning("Models disagree on the side; research signal only.")
            st.caption("Consensus isn't necessarily an executable price. Check current bookmaker odds, vig and changes.")
