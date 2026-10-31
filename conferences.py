"""Conference filters for the 2026 schedule. Display-only; not model inputs.

Mapping includes FBS 2026 teams; unrecognized teams are always "Other / Unmapped".
Review and update for realignment each year. No inference from rankings.
"""
TEAMS = {
 'Big Ten': '''Illinois Northwestern Indiana Purdue Iowa Nebraska Minnesota Wisconsin Michigan Michigan State Ohio State Penn State Maryland Rutgers Oregon Washington UCLA USC''',
 'SEC': '''Alabama Auburn Arkansas LSU Ole Miss Mississippi State Tennessee Vanderbilt Kentucky Florida Georgia South Carolina Missouri Texas Oklahoma Texas A&M''',
 'ACC': '''Boston College Clemson Duke Florida State Georgia Tech Louisville Miami North Carolina NC State Pittsburgh Syracuse Virginia Virginia Tech Wake Forest California Stanford SMU''',
 'Big 12': '''Arizona Arizona State Baylor BYU Cincinnati Colorado Houston Iowa State Kansas Kansas State Oklahoma State TCU Texas Tech UCF Utah West Virginia''',
 'Pac-12': '''Oregon State Washington State Boise State Colorado State Fresno State San Diego State Texas State Utah State''',
 'American': '''Army Navy Charlotte East Carolina Florida Atlantic Memphis North Texas Rice South Florida Temple Tulane Tulsa UAB UTSA''',
 'Sun Belt': '''App State Arkansas State Coastal Carolina Georgia Southern Georgia State James Madison Louisiana Louisiana Monroe Marshall Old Dominion South Alabama Southern Miss Troy''',
 'Conference USA': '''Delaware FIU Jacksonville State Kennesaw State Liberty Louisiana Tech Middle Tennessee Missouri State New Mexico State Sam Houston UTEP Western Kentucky''',
 'Mountain West': '''Air Force Hawaii Nevada New Mexico Northern Illinois San Jose State UNLV Wyoming''',
 'MAC': '''Akron Ball State Bowling Green Buffalo Central Michigan Eastern Michigan Kent State Miami (OH) Ohio Toledo UMass Western Michigan''',
 'Independent': '''Notre Dame UConn''',
}
# Use explicit canonical schools instead of splitting multi-word names.
CANONICAL = {
 'Big Ten': ['Illinois','Northwestern','Indiana','Purdue','Iowa','Nebraska','Minnesota','Wisconsin','Michigan','Michigan State','Ohio State','Penn State','Maryland','Rutgers','Oregon','Washington','UCLA','USC'],
 'SEC':['Alabama','Auburn','Arkansas','LSU','Ole Miss','Mississippi State','Tennessee','Vanderbilt','Kentucky','Florida','Georgia','South Carolina','Missouri','Texas','Oklahoma','Texas A&M'],
 'ACC':['Boston College','Clemson','Duke','Florida State','Georgia Tech','Louisville','Miami','North Carolina','NC State','Pittsburgh','Syracuse','Virginia','Virginia Tech','Wake Forest','California','Stanford','SMU'],
 'Big 12':['Arizona','Arizona State','Baylor','BYU','Cincinnati','Colorado','Houston','Iowa State','Kansas','Kansas State','Oklahoma State','TCU','Texas Tech','UCF','Utah','West Virginia'],
 'Pac-12':['Oregon State','Washington State','Boise State','Colorado State','Fresno State','San Diego State','Texas State','Utah State'],
 'American':['Army','Navy','Charlotte','East Carolina','Florida Atlantic','Memphis','North Texas','Rice','South Florida','Temple','Tulane','Tulsa','UAB','UTSA'],
 'Sun Belt':['App State','Arkansas State','Coastal Carolina','Georgia Southern','Georgia State','James Madison','Louisiana','Louisiana Monroe','Marshall','Old Dominion','South Alabama','Southern Miss','Troy'],
 'Conference USA':['Delaware','FIU','Jacksonville State','Kennesaw State','Liberty','Louisiana Tech','Middle Tennessee','Missouri State','New Mexico State','Sam Houston','UTEP','Western Kentucky'],
 'Mountain West':['Air Force','Hawaii','Nevada','New Mexico','Northern Illinois','San Jose State','UNLV','Wyoming'],
 'MAC':['Akron','Ball State','Bowling Green','Buffalo','Central Michigan','Eastern Michigan','Kent State','Miami (OH)','Ohio','Toledo','UMass','Western Michigan'],
 'Independent':['Notre Dame','UConn'],
}
ALIASES={'Mississippi':'Ole Miss','Mississippi Rebels':'Ole Miss','Miami (FL)':'Miami','Miami FL':'Miami','Miami Hurricanes':'Miami','Miami (OH) RedHawks':'Miami (OH)','Miami RedHawks':'Miami (OH)','NC State':'NC State','North Carolina State':'NC State','Southern Mississippi':'Southern Miss','Appalachian State':'App State','Louisiana-Monroe':'Louisiana Monroe','Louisiana Ragin Cajuns':'Louisiana','UTEP Miners':'UTEP','Connecticut':'UConn'}
# Avoid wrong matches for ambiguous prefixes like "Texas" vs "Texas Tech".
_ENTRIES=sorted(((school,conf) for conf,schools in CANONICAL.items() for school in schools),key=lambda x:-len(x[0]))
def conference_for(name):
    n=str(name or '').strip()
    n=ALIASES.get(n,n)
    for school,conf in _ENTRIES:
        if n==school or n.startswith(school+' '):
            return conf
    return 'Other / Unmapped'

def game_in_conference(game,conf):
    if conf=='All conferences':return True
    home=game.get('home') if isinstance(game,dict) else game.home
    away=game.get('away') if isinstance(game,dict) else game.away
    return conf in (conference_for(home),conference_for(away))
