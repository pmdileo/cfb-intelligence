"""One-time guarded patch for a verified v0.7.4 app.py.
Run from repo root after uploading package files into same tree.
"""
from pathlib import Path
import ast
app=Path('app.py')
s=app.read_text(encoding='utf-8')
if 'render_edge_selected' in s:
    print('Already installed; skip')
    raise SystemExit(0)
assert 'def render_matchup(game):' in s, 'v0.7.4 shared matchup renderer required; merge/install v0.7.4 first'
assert 'render_edge_week(forecasts, shadow_research_by_id, current_odds, now, season, week, render_matchup)' in s
s=s.replace('from cfb.edge_week_ui import render_edge_week',
'''from cfb.edge_select_ui import render_edge_selected
from cfb.briefing_ui import render_quick_brief, render_nil_panel''')
s=s.replace('render_edge_week(forecasts, shadow_research_by_id, current_odds, now, season, week, render_matchup)',
'''render_edge_selected(forecasts, shadow_research_by_id, current_odds, now, season, week, render_matchup)''')
anchor='    g = namedtuple(\'Matchup\', list(game.keys()))(**game)'
assert anchor in s
s=s.replace(anchor, anchor+'''
    with st.expander('Quick game briefing and NIL comparison', expanded=False):
        render_quick_brief(game, shadow_research_by_id)
        render_nil_panel(game)
''')
# Make existing dense chart+comparison an optional deep dive, without restructuring columns.
# Avoid brittle indentation rewriting; retain full detail, currently available on expand.
# Compact header labels are supported inside original expander; no imaginary Apex projection.
needle="    with st.expander(title + (' · FINAL' if g.completed else '')):"
assert needle in s
s=s.replace(needle,"    with st.expander(title + (' · FINAL' if g.completed else '')):",1)
ast.parse(s)
app.write_text(s,encoding='utf-8')
print('v0.7.5 integration applied')
