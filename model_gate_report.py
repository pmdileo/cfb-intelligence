"""Read-only report comparing production baseline to experimental shadow model."""
import argparse
import json
from pathlib import Path
from cfb.data import load_games
from cfb.advanced import load_boxscores
from cfb.model import build_predictions
from cfb.shadow_ratings import replay
from cfb.promotion_gate import assess


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--test-seasons',nargs='+',type=int,required=True)
    parser.add_argument('--min-games',type=int,default=100)
    parser.add_argument('--min-seasons',type=int,default=2)
    parser.add_argument('--output',default=None)
    args=parser.parse_args()
    games=load_games()
    baseline=build_predictions(games,boxscores=load_boxscores())
    shadow=replay(games)
    report=assess(baseline,shadow,test_seasons=args.test_seasons,
                  min_games=args.min_games,min_seasons=args.min_seasons)
    content=json.dumps(report,indent=2)
    print(content)
    if args.output:
        path=Path(args.output)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(content+'\n',encoding='utf-8')

if __name__=='__main__':
    main()
