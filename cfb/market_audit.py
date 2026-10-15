"""Read-only diagnostics for historical market coverage and provider dispersion.

Historical CFBD lines have UNVERIFIED collection/publication timing.  Do not
use these diagnostics to claim recorded pre-kickoff betting performance.
"""
from __future__ import annotations
from collections import Counter
import statistics


def provider_rows(market):
    """Normalize provider spread as HOME projected margin (positive = home favored)."""
    results = []
    for name, values in sorted((market or {}).get('providers', {}).items()):
        if not isinstance(values, dict):
            continue
        spread, total = values.get('home_spread'), values.get('total')
        try:
            spread = -float(spread) if spread is not None else None
            total = float(total) if total is not None else None
        except (TypeError, ValueError):
            continue
        if spread is not None or total is not None:
            results.append({'provider': name, 'home_margin': spread, 'total': total})
    return results


def market_summary(market):
    """Report actual stored consensus, provider ranges, and missing fields."""
    rows = provider_rows(market)
    spreads = [r['home_margin'] for r in rows if r['home_margin'] is not None]
    totals = [r['total'] for r in rows if r['total'] is not None]
    return {
        'provider_count': len(rows),
        'median_home_margin': statistics.median(spreads) if spreads else None,
        'median_total': statistics.median(totals) if totals else None,
        'spread_range': max(spreads) - min(spreads) if len(spreads) >= 2 else None,
        'total_range': max(totals) - min(totals) if len(totals) >= 2 else None,
    }


def coverage_report(games, markets):
    """Season-level coverage of unique ESPN games, no double-counted IDs."""
    by_season = {}
    for g in games:
        try:
            season = int(g['season'])
            gid = str(g['id'])
        except (KeyError, ValueError, TypeError):
            continue
        by_season.setdefault(season, {})[gid] = g
    report=[]
    for season, season_games in sorted(by_season.items(), reverse=True):
        total = len(season_games)
        matched = [markets[str(gid)] for gid in season_games if str(gid) in markets]
        spreads = sum(m.get('market_home_margin') is not None for m in matched)
        totals = sum(m.get('market_total') is not None for m in matched)
        providers = Counter(name for m in matched for name in m.get('providers', {}))
        report.append({
            'season': season, 'games': total, 'matched': len(matched),
            'spread_games': spreads, 'total_games': totals,
            'coverage_pct': round(100 * len(matched) / total, 1) if total else 0.0,
            'providers': ', '.join(f'{n}: {v}' for n, v in providers.most_common(5)),
        })
    return report
