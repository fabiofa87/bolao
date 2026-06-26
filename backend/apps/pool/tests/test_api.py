from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Invite, PoolGroup
from apps.pool.models import Match, Prediction, Team

User = get_user_model()


@pytest.mark.django_db
def test_login_requires_csrf_token():
    User.objects.create_user(
        email="ana@example.com", password="senha-segura", display_name="Ana"
    )
    client = APIClient(enforce_csrf_checks=True)
    response = client.get("/api/auth/session/")
    csrf_token = response.data["csrf_token"]

    rejected = client.post(
        "/api/auth/login/",
        {"email": "ana@example.com", "password": "senha-segura"},
        format="json",
    )
    accepted = client.post(
        "/api/auth/login/",
        {"email": "ana@example.com", "password": "senha-segura"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert rejected.status_code == 403
    assert accepted.status_code == 200


@pytest.mark.django_db
def test_invite_can_only_be_used_once():
    admin = User.objects.create_superuser(
        email="admin@example.com", password="senha-segura", display_name="Admin"
    )
    _, token = Invite.issue(
        email="bia@example.com", display_name="Bia", created_by=admin
    )
    client = APIClient(enforce_csrf_checks=True)
    response = client.get("/api/auth/session/")
    csrf_token = response.data["csrf_token"]
    payload = {"token": token, "display_name": "Bia", "password": "senha-segura"}

    first = client.post(
        "/api/auth/activate/", payload, format="json", HTTP_X_CSRFTOKEN=csrf_token
    )
    client.logout()
    response = client.get("/api/auth/session/")
    csrf_token = response.data["csrf_token"]
    second = client.post(
        "/api/auth/activate/", payload, format="json", HTTP_X_CSRFTOKEN=csrf_token
    )
    assert first.status_code == 201
    assert second.status_code == 400


@pytest.mark.django_db
def test_shared_invite_can_register_multiple_users_in_group():
    admin = User.objects.create_superuser(
        email="admin@example.com", password="senha-segura", display_name="Admin"
    )
    group = PoolGroup.objects.create(name="Amigos", slug="amigos")
    _, token = Invite.issue(
        kind=Invite.Kind.SHARED,
        pool_group=group,
        created_by=admin,
        max_uses=2,
    )
    client = APIClient(enforce_csrf_checks=True)
    response = client.get("/api/auth/session/")
    csrf_token = response.data["csrf_token"]

    info = client.get(f"/api/auth/invite/?token={token}")
    first = client.post(
        "/api/auth/activate/",
        {
            "token": token,
            "email": "ana@example.com",
            "display_name": "Ana",
            "password": "senha-segura",
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    client.logout()
    response = client.get("/api/auth/session/")
    csrf_token = response.data["csrf_token"]
    second = client.post(
        "/api/auth/activate/",
        {
            "token": token,
            "email": "bia@example.com",
            "display_name": "Bia",
            "password": "senha-segura",
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    client.logout()
    response = client.get("/api/auth/session/")
    csrf_token = response.data["csrf_token"]
    third = client.post(
        "/api/auth/activate/",
        {
            "token": token,
            "email": "caio@example.com",
            "display_name": "Caio",
            "password": "senha-segura",
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert info.status_code == 200
    assert info.data["is_shared"] is True
    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 400
    assert User.objects.get(email="ana@example.com").pool_groups.get() == group


@pytest.mark.django_db
def test_other_predictions_are_hidden_until_lock():
    ana = User.objects.create_user(
        email="ana@example.com", password="senha-segura", display_name="Ana"
    )
    bia = User.objects.create_user(
        email="bia@example.com", password="senha-segura", display_name="Bia"
    )
    match = Match.objects.create(
        stage="GROUP_STAGE",
        kickoff_at=timezone.now() + timedelta(hours=1),
        home_team=Team.objects.create(name="Brasil"),
        away_team=Team.objects.create(name="Japão"),
    )
    Prediction.objects.create(user=ana, match=match, home_score=2, away_score=0)
    Prediction.objects.create(user=bia, match=match, home_score=1, away_score=0)
    client = APIClient()
    client.force_authenticate(ana)

    open_response = client.get(f"/api/matches/{match.id}/")
    match.kickoff_at = timezone.now() + timedelta(minutes=10)
    match.save(update_fields=["kickoff_at"])
    locked_response = client.get(f"/api/matches/{match.id}/")

    assert open_response.data["predictions"] == []
    assert len(locked_response.data["predictions"]) == 2
