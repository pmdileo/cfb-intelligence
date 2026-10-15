from cfb.market_audit import coverage_report, market_summary, provider_rows


def test_spread_sign_and_provider_ranges():
    market={'providers':{'A':{'home_spread':-3.5,'total':50.5},
                         'B':{'home_spread':-4.5,'total':52.5}}}
    rows=provider_rows(market)
    assert [r['home_margin'] for r in rows]==[3.5,4.5]
    report=market_summary(market)
    assert report['median_home_margin']==4.0
    assert report['spread_range']==1.0
    assert report['total_range']==2.0


def test_away_favorite_and_missing_prices():
    assert provider_rows({'providers':{'A':{'home_spread':7,'total':None}}})[0]['home_margin']==-7
    assert provider_rows({'providers':{'A':{'home_spread':None,'total':47}}})[0]['total']==47
    assert provider_rows({'providers':{'A':{'home_spread':'oops','total':46}}})==[]


def test_coverage_and_unique_games():
    games=[{'id':'1','season':2025},{'id':'2','season':2025},
           {'id':'1','season':2025},{'id':'3','season':2026}]
    markets={'1':{'market_home_margin':1.5,'market_total':None,'providers':{'A':{}}},
             '3':{'market_home_margin':None,'market_total':44,'providers':{'B':{}}}}
    rows=coverage_report(games,markets)
    assert rows[0]['season']==2026 and rows[0]['games']==1
    assert rows[1]['games']==2
    assert rows[1]['matched']==1 and rows[1]['coverage_pct']==50.0
    assert rows[1]['spread_games']==1 and rows[1]['total_games']==0
