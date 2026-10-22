"""Display current odds separately from unverified historical CFBD market lines."""
import streamlit as st
from .current_odds import freshness, utc


def render_current_odds(market, home, away, kickoff=None):
    st.markdown('**Sportsbook lines · recently observed**')
    state = freshness(market)
    if state == 'unavailable':
        st.caption('No recently observed sportsbook feed matched for this game. Historical lines below are not current quotes.')
        return
    timestamp = market.get('collected_at', 'unknown')
    st.caption(f"Observed: {timestamp} UTC · {market.get('source','Odds feed')}")
    if kickoff and market.get('collected_at') and utc(market['collected_at']) >= utc(kickoff):
        st.warning('Observed at or after kickoff — not a pregame market quote.')
        return
    if state != 'recent':
        st.warning('STALE OR INVALID — older than 48 hours, or an invalid timestamp. Not a current market quote.')
        return
    mm, total = market.get('market_home_margin'), market.get('market_total')
    if mm is not None:
        fav = home if mm > 0 else away if mm < 0 else 'Pick em'
        st.write(f"Spread: **{fav} {'-'+format(abs(mm),'.1f') if mm else '(even)'}**")
    if total is not None:
        st.write(f"Total: **{total:.1f}**")
    st.caption(f"Consensus from {market.get('provider_count',0)} provider(s). Not guaranteed identical to sportsbook quotes now.")
    with st.expander('Bookmaker observations'):
        for provider, quote in sorted((market.get('providers') or {}).items()):
            sp = quote.get('home_spread')
            st.write(f"{provider}: home spread {sp if sp is not None else '—'}; total {quote.get('total', '—')}; updated {quote.get('last_update','unknown')}")
