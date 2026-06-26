from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import DailyChatMessage, PoolGroup

User = get_user_model()


@pytest.mark.django_db
def test_daily_chat_is_limited_to_user_group():
    group_a = PoolGroup.objects.create(name="Grupo A", slug="grupo-a")
    group_b = PoolGroup.objects.create(name="Grupo B", slug="grupo-b")
    ana = User.objects.create_user(
        email="ana@example.com", password="senha-segura", display_name="Ana"
    )
    bia = User.objects.create_user(
        email="bia@example.com", password="senha-segura", display_name="Bia"
    )
    ana.pool_groups.add(group_a)
    bia.pool_groups.add(group_b)
    DailyChatMessage.objects.create(
        pool_group=group_a,
        user=ana,
        body="Mensagem A",
        chat_date=timezone.localdate(),
    )
    DailyChatMessage.objects.create(
        pool_group=group_b,
        user=bia,
        body="Mensagem B",
        chat_date=timezone.localdate(),
    )
    client = APIClient()
    client.force_authenticate(ana)

    response = client.get("/api/chat/")

    assert response.status_code == 200
    assert [message["body"] for message in response.data["messages"]] == ["Mensagem A"]


@pytest.mark.django_db
def test_daily_chat_post_uses_authenticated_user_group():
    group = PoolGroup.objects.create(name="Grupo", slug="grupo")
    ana = User.objects.create_user(
        email="ana@example.com", password="senha-segura", display_name="Ana"
    )
    ana.pool_groups.add(group)
    client = APIClient()
    client.force_authenticate(ana)

    response = client.post("/api/chat/", {"body": "Bom dia"}, format="json")

    assert response.status_code == 201
    assert DailyChatMessage.objects.get().pool_group == group
    assert DailyChatMessage.objects.get().user == ana


@pytest.mark.django_db
def test_prune_daily_chat_removes_previous_days():
    group = PoolGroup.objects.create(name="Grupo", slug="grupo")
    ana = User.objects.create_user(
        email="ana@example.com", password="senha-segura", display_name="Ana"
    )
    DailyChatMessage.objects.create(
        pool_group=group,
        user=ana,
        body="Ontem",
        chat_date=timezone.localdate() - timedelta(days=1),
    )
    DailyChatMessage.objects.create(
        pool_group=group,
        user=ana,
        body="Hoje",
        chat_date=timezone.localdate(),
    )

    call_command("prune_daily_chat")

    assert list(DailyChatMessage.objects.values_list("body", flat=True)) == ["Hoje"]

