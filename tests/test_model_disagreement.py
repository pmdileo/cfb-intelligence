import pytest
from cfb.model_disagreement import describe


def fixtures():
    elo = dict(home_margin=3.5,total=54,elo_contribution=1,venue_contribution=2.5,
               form_contribution=.5,sos_contribution=-.5,ypp_contribution=0)
    shadow = dict(home_margin=-2,total=52,shadow_home_offense_offset=-2,
                  shadow_away_offense_offset=1,shadow_home_defense_offset=0,
                  shadow_away_defense_offset=0,shadow_home_field_per_team=.5)
    return elo,shadow


def test_margin_gap_and_opposite_winners():
    e,s=fixtures(); d=describe(e,s)
    assert d['opposite_winners'] is True
    assert d['shadow_minus_elo'] == -5.5
    assert sum(x['points_to_home'] for x in d['elo_parts']) == pytest.approx(3.5)
    assert sum(x['points_to_home'] for x in d['shadow_parts']) == pytest.approx(-2)


def test_missing_components_are_not_fabricated():
    e,s=fixtures(); s.pop('shadow_home_offense_offset')
    d=describe(e,s)
    assert not d['has_exact_shadow_parts']
    assert d['shadow_parts']==[]


def test_no_shadow():
    e,_=fixtures()
    assert describe(e,None) is None


def test_neutral_field_component():
    e,s=fixtures();s['shadow_home_field_per_team']=0
    s['home_margin']=-3
    d=describe(e,s)
    assert sum(x['points_to_home'] for x in d['shadow_parts']) == pytest.approx(-3)
