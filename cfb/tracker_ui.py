"""Compact three-result strips embedded in the main weekly matchup view."""
import html
import streamlit as st
from .tracker import record

STYLE = {
    'win': ('#17683c', '#e5f5e9', '✓ WIN'),
    'loss': ('#a72c31', '#fbe8e8', '✕ LOSS'),
    'push': ('#555555', '#f0f0f0', '— PUSH'),
    'pending': ('#555555', '#f0f0f0', '◷ PENDING'),
    'no_line': ('#555555', '#f0f0f0', '— NO LINE'),
    'no_pick': ('#555555', '#f0f0f0', '— NO PICK'),
}


def render_result_strip(status, provenance):
    """One game, three independently colored results."""
    cells = []
    for key, label in [('su', 'WINNER (SU)'), ('ats', 'SPREAD (ATS)'), ('ou', 'OVER / UNDER')]:
        fg, bg, word = STYLE[status[key]]
        cells.append(
            f'<div style="flex:1;min-width:0;border-radius:8px;padding:11px 4px;'
            f'text-align:center;background:{bg};color:{fg}">'
            f'<div style="font-size:.73em;font-weight:700">{html.escape(label)}</div>'
            f'<div style="font-size:.9em;font-weight:700">{html.escape(word)}</div></div>'
        )
    st.markdown('<div style="display:flex;gap:5px;margin:6px 0 10px">' + ''.join(cells) + '</div>',
                unsafe_allow_html=True)
    if provenance == 'retrospective':
        st.caption('RETROSPECTIVE · Reconstructed from historical results; not a saved pregame prediction.')
    elif provenance == 'archived':
        st.caption('ARCHIVED · First forecast saved before kickoff.')


def render_records(archived_rows, season, week):
    """Official record is restricted to genuinely archived pregame forecasts."""
    season_rows = [r for r in archived_rows if int(r['season']) == int(season)]
    groups = [('This week', [r for r in season_rows if int(r['week']) == int(week)]),
              ('Season (archived)', season_rows)]
    for heading, rows in groups:
        st.markdown('**' + heading + '**')
        cols = st.columns(3)
        for col, key, label in zip(cols, ('su', 'ats', 'ou'), ('Winner', 'Against spread', 'Over/Under')):
            summary = record(rows, key)
            caption = f"{summary['pct']:.1%} of graded picks" if summary['pct'] is not None else 'No graded picks yet'
            col.metric(label, f"{summary['wins']}–{summary['losses']}", caption)
    st.caption('Official records exclude retrospective games. Pushes and games without pregame market lines do not count as wins or losses.')
