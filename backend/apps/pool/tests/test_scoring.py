import pytest
from django.contrib.auth import get_user_model

from apps.pool.models import Match, Prediction, ScoringRule, Team
from apps.pool.services import calculate_points

User = get_user_model()


@pytest.fixture
def prediction(db):
    user = User.objects.create_user(
        email="jogador@example.com", password="senha-segura", display_name="Jogador"
    )
    home = Team.objects.create(name="Brasil")
    away = Team.objects.create(name="Japão")
    match = Match.objects.create(
        stage="GROUP_STAGE",
        kickoff_at="2026-06-20T19:00:00Z",
        home_team=home,
        away_team=away,
        scoring_home=2,
        scoring_away=1,
    )
    return Prediction(user=user, match=match, home_score=2, away_score=1)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("guess", "result", "expected"),
    [
        ((2, 1), (2, 1), 5),
        ((3, 0), (2, 1), 2),
        ((2, 0), (2, 1), 3),
        ((1, 1), (2, 2), 3),
        ((0, 1), (2, 1), 0),
    ],
)
def test_scoring_matrix(prediction, guess, result, expected):
    prediction.home_score, prediction.away_score = guess
    prediction.match.scoring_home, prediction.match.scoring_away = result
    assert calculate_points(prediction, prediction.match, ScoringRule.current()) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "stage",
    [
        "GROUP_STAGE",
        "LAST_32",
        "ROUND_OF_32",
        "LAST_16",
        "ROUND_OF_16",
        "QUARTER_FINALS",
        "QUARTER_FINAL",
        "SEMI_FINALS",
        "SEMI_FINAL",
        "THIRD_PLACE",
        "THIRD_PLACE_PLAYOFF",
        "THIRD_PLACE_PLAY_OFF",
        "FINAL",
    ],
)
def test_all_stages_use_base_points(prediction, stage):
    prediction.match.stage = stage
    assert calculate_points(prediction, prediction.match, ScoringRule.current()) == 5
