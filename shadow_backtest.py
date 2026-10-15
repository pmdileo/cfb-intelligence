"""Run from repository root; read-only. Prints season-level baseline/shadow comparisons."""
import json
from cfb.data import load_games
from cfb.advanced import load_boxscores
from cfb.shadow_evaluation import compare

if __name__ == '__main__':
    print(json.dumps(compare(load_games(), load_boxscores()), indent=2))
