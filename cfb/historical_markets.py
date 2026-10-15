"""Retrospective grading against CFBD historical market consensus.

Historical CFBD lines have unverified publication times. These results are
research-only and MUST NOT be mixed into the verified live prediction record.
"""
from .tracker import grade_game


def retrospective_grade(prediction, market):
    """Return grading for a completed historical game, with market data if present."""
    item = dict(prediction)
    if market:
        item['market_home_margin'] = market.get('market_home_margin')
        item['market_total'] = market.get('market_total')
    return grade_game(item, prediction)


def historical_rows(predictions, market_lines):
    """Grade historical games only; never mutate underlying forecasts."""
    result = []
    for game in predictions:
        if not game.get('completed') or game.get('home_score') is None or game.get('away_score') is None:
            continue
        market = market_lines.get(str(game['id']))
        result.append({**game, 'status': retrospective_grade(game, market),
                       'provenance': 'retrospective', 'has_historical_market': bool(market)})
    return result
