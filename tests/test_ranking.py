import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from campwatcher.config import config
from ranking import difficulty_score


def test_difficulty_score_returns_float(monkeypatch):
    monkeypatch.setattr(
        "ranking._fetch_availability",
        lambda *args, **kwargs: {"campsites": {}},
    )
    result = difficulty_score("100")
    assert isinstance(result, float)
