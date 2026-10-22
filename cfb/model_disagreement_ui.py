"""Expandable, explicitly model-derived explanation for a matchup."""
import pandas as pd
import streamlit as st
from .model_disagreement import describe


def render_disagreement(official, shadow):
    if not shadow:
        return
    details = describe(official, shadow)
    with st.expander('🔎 Why do Elo and Shadow disagree?', expanded=False):
        home, away = str(official['home']), str(official['away'])
        a,b,c = st.columns(3)
        a.metric('Official Elo home margin', f"{details['elo_margin']:+.1f}")
        b.metric('Shadow home margin', f"{details['shadow_margin']:+.1f}")
        c.metric('Shadow − Elo', f"{details['shadow_minus_elo']:+.1f} pts")
        st.caption(f'All margins use {home} minus {away}. Positive favors {home}; negative favors {away}.')
        if details['opposite_winners']:
            st.warning('The two models favor different outright winners.')
        st.markdown('**Official Elo: what contributes to its projected margin**')
        st.dataframe(pd.DataFrame(details['elo_parts']).rename(columns={
            'factor':'Factor','points_to_home':'Points toward home margin'}),
            hide_index=True,use_container_width=True)
        st.markdown('**Shadow: how it builds its predicted score**')
        if details['has_exact_shadow_parts']:
            st.dataframe(pd.DataFrame(details['shadow_parts']).rename(columns={
                'factor':'Factor','points_to_home':'Points toward home margin'}),
                hide_index=True,use_container_width=True)
            st.caption('Shadow scoring uses a 27.5-point league prior per team, '
                       'plus its learned offense and opposing-defense offsets, and home field. '
                       'The league priors cancel when calculating the margin. ' 
                       'The residual captures rounding or clipping at zero points.')
        else:
            st.info('The cached Shadow forecast does not include component-level ratings yet. '
                    'They become available after the updated replay is installed and recomputed.')
        st.write(f"Projected totals: **Elo {details['elo_total']:.1f}** vs "
                 f"**Shadow {details['shadow_total']:.1f}**. "
                 f"Difference: **{details['shadow_total']-details['elo_total']:+.1f} points**.")
        st.caption('These are explanations of two heuristic algorithms, not verified causes '
                   'of the game outcome. Shadow does not separately ingest player injuries, '
                   'recruiting, NIL, or coaching factors; Elo and Shadow use different training signals.')
