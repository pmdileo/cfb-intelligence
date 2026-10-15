from cfb.tournament import tournament,calibration_rows,picks_record

def game(id,margin,prob=.6,season=2025):
 return dict(id=str(id),home_id='H',away_id='A',home='Home',away='Away',date=f'{season}-10-01T12:00:00Z',season=season,week=5,completed=True,home_score=24,away_score=21,home_margin=margin,total=45,home_win_prob=prob)

def test_pairs_and_records():
 a=[game(1,6),game(2,-2)];b=[game(1,4),game(2,2)]
 result=tournament(a,b,{'1':{'market_home_margin':2,'market_total':40}},[2025])
 assert result['paired_games']==2
 assert len(result['details'])==2
 assert picks_record(result['details'],'baseline','ats')['win']==1
 assert picks_record(result['details'],'shadow','ats')['win']==1
 assert picks_record(result['details'],'baseline','ats')['no_line']==1

def test_calibration_counts():
 r=tournament([game(1,6,.71)],[game(1,5,.65)],{},[2025]);vals=calibration_rows(r['details'],'baseline')
 assert len(vals)==1 and vals[0]['games']==1 and vals[0]['observed_home_win_rate']==1

def test_selected_season():
 a=[game(1,4,season=2024),game(2,4,season=2025)]
 assert tournament(a,a,{},[2025])['paired_games']==1

def test_does_not_mutate_or_promote():
 x=game(1,4);orig=x.copy();tournament([x],[game(1,5)],{},[2025]);assert x==orig
