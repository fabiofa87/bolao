import pytest

from apps.pool.models import Match
from apps.pool.sync import apply_matches, extract_scores


def test_penalties_are_removed_from_scoring_score():
    values = extract_scores(
        {
            "fullTime": {"home": 6, "away": 5},
            "extraTime": {"home": 0, "away": 0},
            "penalties": {"home": 5, "away": 4},
        }
    )
    assert (values["scoring_home"], values["scoring_away"]) == (1, 1)


@pytest.mark.django_db
def test_manual_match_is_not_overwritten():
    payload = {
        "matches": [
            {
                "id": 99,
                "stage": "GROUP_STAGE",
                "group": "GROUP_A",
                "matchday": 1,
                "utcDate": "2026-06-20T19:00:00Z",
                "status": "FINISHED",
                "lastUpdated": "2026-06-20T22:00:00Z",
                "homeTeam": {"id": 1, "name": "Brasil", "shortName": "Brasil", "tla": "BRA"},
                "awayTeam": {"id": 2, "name": "Japão", "shortName": "Japão", "tla": "JPN"},
                "score": {"fullTime": {"home": 2, "away": 0}},
            }
        ]
    }
    apply_matches(payload)
    match = Match.objects.get(provider_id=99)
    match.manual_override = True
    match.scoring_home = 1
    match.scoring_away = 1
    match.save()
    apply_matches(payload)
    match.refresh_from_db()
    assert (match.scoring_home, match.scoring_away) == (1, 1)


@pytest.mark.django_db
def test_future_knockout_match_accepts_unknown_teams():
    payload = {
        "matches": [
            {
                "id": 100,
                "stage": "LAST_16",
                "group": None,
                "matchday": None,
                "utcDate": "2026-07-01T19:00:00Z",
                "status": "SCHEDULED",
                "lastUpdated": "2026-06-20T22:00:00Z",
                "homeTeam": {"id": None, "name": None},
                "awayTeam": {"id": None, "name": None},
                "score": {},
            }
        ]
    }
    apply_matches(payload)
    match = Match.objects.get(provider_id=100)
    assert match.home_team_id != match.away_team_id
    assert match.home_team.short_name == "A definir"
