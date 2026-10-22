"""View actual archived forward Shadow research metrics; does not grade ATS/O-U."""
import json
from cfb.data import load_games
from cfb.shadow_forward import forward_results

if __name__ == '__main__':
    report=forward_results(load_games())
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
