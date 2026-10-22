"""Run on scheduled GitHub workflow; saves only future Shadow research picks."""
import json
from cfb.data import load_games
from cfb.shadow_forward import archive

if __name__ == '__main__':
    new=archive(load_games())
    print(json.dumps({'new_shadow_pregame_snapshots':len(new),
                      'note':'Shadow research only; official predictions unchanged.'},indent=2))
