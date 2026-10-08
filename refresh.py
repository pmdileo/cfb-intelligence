"""One command refresh, used by GitHub Actions."""
import argparse
from cfb.data import refresh

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--start',type=int,default=2021)
    parser.add_argument('--end',type=int,default=None)
    parser.add_argument('--pause',type=float,default=.1)
    args=parser.parse_args()
    refresh(start=args.start,end=args.end,pause=args.pause)
