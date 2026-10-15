"""Research-only comparison with an assumed four-hour result delay."""
import json
from cfb.data import load_games
from cfb.advanced import load_boxscores
from cfb.time_safe import replay_baseline, replay_shadow
from cfb.shadow_evaluation import compare
from cfb.model import evaluation
from collections import defaultdict

if __name__=='__main__':
    games=load_games()
    baseline=replay_baseline(games,boxscores=load_boxscores())
    shadow=replay_shadow(games)
    out=[]
    for year in sorted({int(g['season']) for g in games}):
        b=[g for g in baseline if int(g['season'])==year]
        s=[g for g in shadow if int(g['season'])==year]
        if b:
            out.append({'season':year,'baseline':evaluation(b),'shadow':evaluation(s)})
    print(json.dumps({'method':'Assumed 4-hour completion delay, not verified final timestamps',
                      'results':out,'production_model_changed':False},indent=2))
