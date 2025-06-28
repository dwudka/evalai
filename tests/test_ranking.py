import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from campwatcher.config import config
from ranking import difficulty_score


def test_difficulty_score_returns_float(mocker):
    mocker.patch("ranking._fetch_availability", return_value={"campsites": {}})
    result = difficulty_score("100")
    assert isinstance(result, float)
