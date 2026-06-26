import pytest
from django.contrib.auth import get_user_model

from apps.pool.services import build_ranking, import_initial_scores, parse_initial_scores
from apps.accounts.models import PoolGroup

User = get_user_model()


@pytest.mark.django_db
def test_import_is_idempotent_and_ties_share_rank():
    admin = User.objects.create_superuser(
        email="admin@example.com", password="senha-segura", display_name="Admin"
    )
    content = "nome,email,pontos\nAna,ana@example.com,10\nBia,bia@example.com,10\n"
    rows = parse_initial_scores(content.encode())
    import_initial_scores(rows, created_by=admin)
    import_initial_scores(rows, created_by=admin)
    ranking = build_ranking()
    assert [row["rank"] for row in ranking] == [1, 1]
    assert [row["total_points"] for row in ranking] == [10, 10]


@pytest.mark.django_db
def test_ranking_is_filtered_by_user_groups():
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

    ranking = build_ranking(ana)

    assert [row["display_name"] for row in ranking] == ["Ana"]
