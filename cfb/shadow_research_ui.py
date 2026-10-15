"""Clearly segregated experimental prediction display for the production app."""
import streamlit as st


def shadow_label(game, forecast):
    margin = float(forecast['home_margin'])
    if margin > 0: return f"{game['home']} -{margin:.1f}"
    if margin < 0: return f"{game['away']} -{abs(margin):.1f}"
    return 'Pick’em'


def render_shadow_research(game, forecast):
    """No grading, archiving, or official pick mutations."""
    st.markdown('**🔬 Shadow Research Pick**')
    st.caption('EXPERIMENTAL · Not the official prediction or archived betting record')
    if forecast is None:
        st.write('Unavailable for this matchup')
        return
    st.write(f"**{shadow_label(game, forecast)}**")
    st.write(f"Projected score (away–home): **{forecast['away_points']:.0f}–{forecast['home_points']:.0f}**")
    st.write(f"Win probability ({game['home']}): **{forecast['home_win_prob']:.1%}**")
    st.write(f"Projected total: **{forecast['total']:.1f}**")
    st.caption('Research-only replay. Historical results become eligible after an assumed 4-hour game duration; not a verified final-whistle or frozen pregame forecast.')
