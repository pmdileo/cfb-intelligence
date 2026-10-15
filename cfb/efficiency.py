"""Conservative offensive-play reconstruction from ESPN team stat rows.

Only derives offensive plays from clearly named rushing and passing attempts.
A completed pass is not a pass attempt. Missing fields stay missing.
"""
import re


def _value(stat):
    return stat.get('displayValue', stat.get('value'))


def _number(x):
    if x is None or isinstance(x, bool):
        return None
    s = str(x).replace(',', '').strip()
    if not re.fullmatch(r'\d+(?:\.\d+)?', s):
        return None
    return float(s)


def team_metrics(stats):
    fields = {}
    for stat in stats or []:
        for label in (stat.get('name'), stat.get('label')):
            if label:
                fields[re.sub(r'[^a-z0-9]', '', str(label).lower())] = _value(stat)

    def get(*names):
        for name in names:
            key = re.sub(r'[^a-z0-9]', '', name.lower())
            val = _number(fields.get(key))
            if val is not None:
                return val
        return None

    yards = get('totalYards', 'total yards')
    plays = get('totalOffensivePlays', 'totalPlays', 'offensivePlays')
    rush = get('rushingAttempts', 'rushing attempts', 'rushingAtt')
    passing = get('passingAttempts', 'passing attempts', 'passingAtt')
    # Often ESPN presents passing as completions/attempts rather than attempts alone.
    if passing is None:
        for name in ('completionattempts', 'completionsattempts', 'completionspassingattempts'):
            raw = str(fields.get(name, ''))
            match = re.fullmatch(r'\s*\d+\s*/\s*(\d+)\s*', raw)
            if match:
                passing = float(match.group(1))
                break
    if plays is None and rush is not None and passing is not None:
        plays = rush + passing
    ypp = get('yardsPerPlay', 'yardsPerPlayAvg', 'yards per play')
    if ypp is None and yards is not None and plays is not None and plays > 0:
        ypp = yards / plays
    return {
        'total_yards': yards,
        'offensive_plays': plays,
        'yards_per_play': round(ypp, 3) if ypp is not None else None,
        'play_count_source': ('derived_rush_plus_pass' if get('totalOffensivePlays','totalPlays','offensivePlays') is None and plays is not None else 'reported' if plays is not None else 'missing'),
    }


def repair_needed(boxscore):
    return any((entry or {}).get('yards_per_play') is None for entry in (boxscore or {}).values())
