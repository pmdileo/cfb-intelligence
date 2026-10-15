"""Run from repo root; creates reports/research_audit.json; never edits source data."""
import json
from pathlib import Path
from cfb.data import load_games
from cfb.advanced import load_boxscores
from cfb.market_lines import load_lines
from cfb.research_audit import audit

report=audit(load_games(),load_boxscores(),load_lines())
path=Path('reports/research_audit.json');path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,indent=2))
