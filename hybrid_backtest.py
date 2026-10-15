"""Read-only v0.6.2 experimental comparison, run at repository root."""
import json
from cfb.data import load_games
from cfb.advanced import load_boxscores
from cfb.model import build_predictions
from cfb.shadow_ratings import replay
from cfb.hybrid_validation import validate_tournament, kickoff_overlap_audit

if __name__ == '__main__':
    games=load_games()
    baseline=build_predictions(games,boxscores=load_boxscores())
    shadow=replay(games)
    output={'hybrid':validate_tournament(baseline,shadow),
            'kickoff_overlap_risk':kickoff_overlap_audit(games)}
    print(json.dumps(output,indent=2))
