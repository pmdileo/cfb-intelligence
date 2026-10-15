import pytest
from cfb.promotion_gate import assess,aligned_pairs


def game(id,year,margin,total,**changes):
    d=dict(id=str(id),season=year,home_id='1',away_id='2',date=f'{year}-09-01T18:00:00Z',
           completed=True,home_score=28,away_score=21,home_margin=margin,total=total,home_win_prob=.65)
    d.update(changes)
    return d


def test_only_heldout_and_aligned():
    b=[game(1,2024,7,49),game(2,2025,7,49)]
    c=[game(1,2024,8,48),game(2,2025,8,48)]
    assert len(aligned_pairs(b,c,test_seasons=[2025]))==1


def test_require_explicit_season():
    with pytest.raises(ValueError):aligned_pairs([],[],test_seasons=[])


def test_reject_metadata_disagreement():
    with pytest.raises(ValueError):aligned_pairs([game(1,2025,7,49)],[game(1,2025,7,49,home_score=30)],test_seasons=[2025])


def test_small_sample_never_promoted():
    r=assess([game(1,2025,30,70)],[game(1,2025,7,49,home_win_prob=.8)],test_seasons=[2025])
    assert r['decision']=='KEEP_BASELINE' and r['manual_approval_required']


def test_candidate_requires_all_improvements():
    b=[game(1,2024,15,65,home_win_prob=.5),game(2,2025,15,65,home_win_prob=.5)]
    c=[game(1,2024,7,49,home_win_prob=.9),game(2,2025,7,49,home_win_prob=.9)]
    r=assess(b,c,test_seasons=[2024,2025],min_games=2,min_seasons=2)
    assert r['decision']=='REVIEW_CANDIDATE'
    assert r['by_season']['2024']['challenger']['games']==1


def test_missing_prob_keeps_baseline():
    b=[game(1,2024,15,65),game(2,2025,15,65)]
    c=[game(1,2024,7,49,home_win_prob=None),game(2,2025,7,49,home_win_prob=None)]
    assert assess(b,c,test_seasons=[2024,2025],min_games=2,min_seasons=2)['decision']=='KEEP_BASELINE'


def test_no_mutation():
    b=[game(1,2025,10,54)];c=[game(1,2025,7,49)]
    saved=[dict(b[0]),dict(c[0])]
    assess(b,c,test_seasons=[2025],min_games=1,min_seasons=1)
    assert b[0]==saved[0] and c[0]==saved[1]
