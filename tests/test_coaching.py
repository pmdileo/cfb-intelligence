import pytest
from cfb.coaching import load_coaches

def test_missing_file_is_empty(tmp_path):
    assert load_coaches(tmp_path/'none.csv')==[]

def test_mandatory_sources(tmp_path):
    p=tmp_path/'x.csv';p.write_text('season,team_id,team_name,head_coach,source_url,verified_on\n2026,1,Test,Someone,,2026-10-08\n')
    with pytest.raises(ValueError):load_coaches(p)
