from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError

from apps.pool.models import Match, PredictionRevision, Team
from apps.pool.services import save_prediction

User = get_user_model()


@pytest.fixture
def setup_match(db):
    user = User.objects.create_user(
        email="ana@example.com", password="senha-segura", display_name="Ana"
    )
    match = Match.objects.create(
        stage="GROUP_STAGE",
        kickoff_at=timezone.now() + timedelta(hours=1),
        home_team=Team.objects.create(name="Brasil"),
        away_team=Team.objects.create(name="Japão"),
    )
    return user, match


@pytest.mark.django_db
def test_prediction_is_idempotently_updated_with_history(setup_match):
    user, match = setup_match
    first = save_prediction(user=user, match_id=match.id, home_score=2, away_score=0)
    second = save_prediction(user=user, match_id=match.id, home_score=3, away_score=1)
    assert first.id == second.id
    assert PredictionRevision.objects.filter(prediction=second).count() == 1


@pytest.mark.django_db
def test_prediction_locks_exactly_at_deadline(setup_match):
    user, match = setup_match
    with freeze_time(match.lock_at):
        with pytest.raises(ValidationError):
            save_prediction(user=user, match_id=match.id, home_score=1, away_score=0)

