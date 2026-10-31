"""Apply UI-only v0.7.4 to the existing repo; idempotent with explicit guards."""
from pathlib import Path
import shutil
repo=Path(__file__).resolve().parent
app=repo/'app.py'
if not app.exists():
    raise SystemExit('Run this script from repository ROOT (same folder as app.py).')
s=app.read_text(encoding='utf-8')
if 'from cfb.conferences import game_in_conference' in s:
    raise SystemExit('Already installed; no changes made.')
old='from cfb.edge_tab_ui import render_edge_tab'
assert old in s,'Expected v0.7.3 EDGE integration not found; stop to avoid modifying unexpected code.'
s=s.replace(old,'from cfb.conferences import game_in_conference, CANONICAL\nfrom cfb.edge_week_ui import render_edge_week')
needle="    show_completed = st.toggle('Include completed games', value=True)"
assert needle in s
s=s.replace(needle,needle+"\n    st.caption('Conference selection applies only to Matchup Center.')\n    conference = st.selectbox('Matchup conference', ['All conferences'] + list(CANONICAL) + ['Other / Unmapped'])")
needle="if not show_completed:\n    subset = subset[~subset.completed]"
assert needle in s
s=s.replace(needle,needle+"\nsubset = subset[subset.apply(lambda x: game_in_conference(x, conference), axis=1)]")
# Extract the EXISTING full matchup UI verbatim from its loop into a reusable function.
start=s.index('for g in subset.itertuples():\n')
end=s.index("st.divider()\nrender_forward_scoreboard(raw)",start)
block=s[start+len('for g in subset.itertuples():\n'):end]
assert block.startswith('    title ='), 'Mismatch in original matchup block'
# Function receives a dict/series and converts to attribute-access namedtuple.
from_header="def render_matchup(game):\n    from types import SimpleNamespace\n    g = SimpleNamespace(**game)\n"
function=from_header+block
s=s[:start]+"for g in subset.to_dict('records'):\n    render_matchup(g)\n"+s[end:]
old_nav='''if view == "EDGE":
    render_edge_tab(
        forecasts,
        shadow_research_by_id,
        current_odds,
        now
    )
    st.stop()
'''
assert old_nav in s
s=s.replace(old_nav,'')
nav="st.subheader('Matchup center')"
assert nav in s
s=s.replace(nav,'',1)
# Move the whole-matchup renderer before navigation; required by both views.
nav_start=s.index('view = st.radio(')
nav_end=s.index('if subset.empty:',nav_start)
nav_block=s[nav_start:nav_end]
assert 'Matchup center' in nav_block and 'EDGE' in nav_block
s=s[:nav_start]+function+'\n'+nav_block+'''if view == "EDGE":
    render_edge_week(forecasts, shadow_research_by_id, current_odds, now, season, week, render_matchup)
    st.stop()
st.subheader('Matchup center')
'''+s[nav_end:]
# The original block's g is now SimpleNamespace; keep original g._asdict() semantics
# by providing a class with _asdict method.
s=s.replace('    from types import SimpleNamespace\n    g = SimpleNamespace(**game)',
'''    from collections import namedtuple
    g = namedtuple('Matchup', list(game.keys()))(**game)''')
# Render methods use row in their original logic; position invariant.
shutil.copyfile(app,app.with_suffix('.py.v073.bak'))
app.write_text(s,encoding='utf-8')
(repo/'cfb').mkdir(exist_ok=True)
shutil.copyfile(repo/'conferences.py',repo/'cfb/conferences.py')
shutil.copyfile(repo/'edge_week_ui.py',repo/'cfb/edge_week_ui.py')
print('Patched app.py, installed cfb/conferences.py and cfb/edge_week_ui.py')
