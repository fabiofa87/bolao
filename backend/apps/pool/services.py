import csv
import hashlib
import io
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import IntegerField, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import (
    Match,
    PointAdjustment,
    Prediction,
    PredictionRevision,
    ScoringRule,
)

User = get_user_model()

def outcome(home, away):
    if home == away:
        return "DRAW"
    return "HOME" if home > away else "AWAY"


def calculate_points(prediction, match, rule=None):
    if not match.has_result:
        return 0
    rule = rule or ScoringRule.current()
    actual = (match.scoring_home, match.scoring_away)
    guessed = (prediction.home_score, prediction.away_score)

    if guessed == actual:
        return rule.exact_score_points
    if outcome(*guessed) != outcome(*actual):
        return 0

    points = rule.correct_result_points
    if outcome(*actual) == "DRAW":
        return points + rule.wrong_draw_bonus

    winner_index = 0 if actual[0] > actual[1] else 1
    if guessed[winner_index] == actual[winner_index]:
        points += rule.winner_goals_bonus
    return points


@transaction.atomic
def save_prediction(*, user, match_id, home_score, away_score):
    match = Match.objects.select_for_update().get(pk=match_id)
    if timezone.now() >= match.lock_at:
        raise ValidationError({"match": "O prazo para este palpite terminou."})

    prediction, created = Prediction.objects.select_for_update().get_or_create(
        user=user,
        match=match,
        defaults={"home_score": home_score, "away_score": away_score},
    )
    if not created:
        PredictionRevision.objects.create(
            prediction=prediction,
            home_score=prediction.home_score,
            away_score=prediction.away_score,
            changed_by=user,
        )
        prediction.home_score = home_score
        prediction.away_score = away_score
        prediction.save(update_fields=["home_score", "away_score", "updated_at"])
    return prediction


@transaction.atomic
def recalculate_points(match=None):
    predictions = Prediction.objects.select_related("match")
    if match is not None:
        predictions = predictions.filter(match=match)
    rule = ScoringRule.current()
    changed = []
    for prediction in predictions:
        new_points = calculate_points(prediction, prediction.match, rule)
        if prediction.points != new_points:
            prediction.points = new_points
            changed.append(prediction)
    if changed:
        Prediction.objects.bulk_update(changed, ["points"])
    return len(changed)


def build_ranking(user=None):
    group_ids = []
    if user is not None and not user.is_staff:
        group_ids = list(user.pool_groups.values_list("id", flat=True))

    correct_result_counts = {}
    finished_predictions = Prediction.objects.select_related("match").filter(
        user__is_active=True,
        user__is_staff=False,
        match__scoring_home__isnull=False,
        match__scoring_away__isnull=False,
    )
    if group_ids:
        finished_predictions = finished_predictions.filter(user__pool_groups__in=group_ids).distinct()
    for prediction in finished_predictions:
        match = prediction.match
        if outcome(prediction.home_score, prediction.away_score) == outcome(
            match.scoring_home, match.scoring_away
        ):
            correct_result_counts[prediction.user_id] = (
                correct_result_counts.get(prediction.user_id, 0) + 1
            )

    prediction_points = (
        Prediction.objects.filter(user_id=OuterRef("pk"))
        .values("user_id")
        .annotate(total=Sum("points"))
        .values("total")
    )
    adjustment_points = (
        PointAdjustment.objects.filter(user_id=OuterRef("pk"))
        .values("user_id")
        .annotate(total=Sum("points"))
        .values("total")
    )
    adjustment_exact_hits = (
        PointAdjustment.objects.filter(user_id=OuterRef("pk"))
        .values("user_id")
        .annotate(total=Sum("exact_hits"))
        .values("total")
    )
    users_queryset = User.objects.filter(is_active=True, is_staff=False)
    if group_ids:
        users_queryset = users_queryset.filter(pool_groups__in=group_ids).distinct()
    users = (
        users_queryset
        .annotate(
            prediction_total=Coalesce(
                Subquery(prediction_points, output_field=IntegerField()), 0
            ),
            adjustment_total=Coalesce(
                Subquery(adjustment_points, output_field=IntegerField()), 0
            ),
            adjustment_exact_hits=Coalesce(
                Subquery(adjustment_exact_hits, output_field=IntegerField()), 0
            ),
        )
        .order_by("display_name", "id")
    )
    rows = []
    for user in users:
        prediction_points = user.prediction_total or 0
        adjustment_points = user.adjustment_total or 0
        rows.append(
            {
                "user_id": user.id,
                "display_name": user.display_name,
                "prediction_points": prediction_points,
                "adjustment_points": adjustment_points,
                "prediction_exact_hits": correct_result_counts.get(user.id, 0),
                "adjustment_exact_hits": user.adjustment_exact_hits or 0,
                "correct_result_hits": correct_result_counts.get(user.id, 0)
                + (user.adjustment_exact_hits or 0),
                "total_points": prediction_points + adjustment_points,
            }
        )
    rows.sort(
        key=lambda row: (
            -row["total_points"],
            -row["correct_result_hits"],
            row["display_name"].lower(),
        )
    )
    previous_key = None
    previous_rank = 0
    for index, row in enumerate(rows, start=1):
        rank_key = (row["total_points"], row["correct_result_hits"])
        if rank_key != previous_key:
            previous_rank = index
            previous_key = rank_key
        row["rank"] = previous_rank
    return rows


@dataclass
class ImportRow:
    line: int
    name: str
    points: int | None
    exact_hits: int = 0
    email: str = ""
    error: str = ""


def decode_csv_content(content):
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Nao foi possivel ler o CSV. Salve o arquivo como UTF-8 ou Windows-1252.")


def normalize_import_header(header, index):
    value = (header or "").strip().lower()
    if not value and index == 0:
        return "nome"
    aliases = {
        "name": "nome",
        "participante": "nome",
        "jogador": "nome",
        "e-mail": "email",
        "mail": "email",
        "pontuacao": "pontos",
        "pontuação": "pontos",
        "score": "pontos",
        "lt": "exact_hits",
        "lts": "exact_hits",
        "cravadas": "exact_hits",
        "cravadas (qtd)": "exact_hits",
        "placar exato": "exact_hits",
        "placar exato (qtd)": "exact_hits",
    }
    return aliases.get(value, value)


def parse_initial_scores(content):
    text = decode_csv_content(content)
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    normalized_headers = [
        normalize_import_header(field, index)
        for index, field in enumerate(reader.fieldnames or [])
    ]
    if not reader.fieldnames or not {"nome", "pontos"}.issubset(set(normalized_headers)):
        raise ValueError("O CSV deve conter nome e pontos. A coluna email e opcional se o participante ja existir.")
    reader.fieldnames = normalized_headers

    rows = []
    for line, raw in enumerate(reader, start=2):
        normalized = {
            (key or "").strip().lower(): (value or "").strip()
            for key, value in raw.items()
        }
        row = ImportRow(
            line=line,
            name=normalized.get("nome", ""),
            email=normalized.get("email", "").lower(),
            points=None,
        )
        try:
            row.points = int(normalized.get("pontos", ""))
        except ValueError:
            row.error = "Pontuacao invalida."
        exact_hits = normalized.get("exact_hits", "")
        if exact_hits:
            try:
                row.exact_hits = int(exact_hits)
            except ValueError:
                row.error = "LT invalido."
        if not row.name:
            row.error = "Nome e obrigatorio."
        if row.email and "@" not in row.email:
            row.error = "E-mail invalido."
        rows.append(row)
    return rows


@transaction.atomic
def import_initial_scores(rows, *, created_by):
    imported = 0
    for row in rows:
        if row.error:
            raise ValueError(f"Linha {row.line}: {row.error}")
        if row.email:
            user, _ = User.objects.get_or_create(
                email=row.email,
                defaults={
                    "display_name": row.name,
                    "is_active": True,
                    "username": row.email,
                },
            )
            import_key = "initial:" + hashlib.sha256(row.email.encode()).hexdigest()
        else:
            users = User.objects.filter(display_name__iexact=row.name, is_staff=False)
            if users.count() != 1:
                raise ValueError(
                    f"Linha {row.line}: informe email ou cadastre exatamente um participante com nome '{row.name}'."
                )
            user = users.get()
            import_key = f"initial:user:{user.id}"
        changed_fields = []
        if user.display_name != row.name:
            user.display_name = row.name
            changed_fields.append("display_name")
        if not user.is_active:
            user.is_active = True
            changed_fields.append("is_active")
        if changed_fields:
            user.save(update_fields=changed_fields)
        default_group, _ = user.pool_groups.model.objects.get_or_create(
            slug="geral", defaults={"name": "Geral"}
        )
        user.pool_groups.add(default_group)
        PointAdjustment.objects.update_or_create(
            import_key=import_key,
            defaults={
                "user": user,
                "points": row.points,
                "exact_hits": row.exact_hits,
                "reason": "Saldo inicial importado",
                "created_by": created_by,
            },
        )
        imported += 1
    return imported
