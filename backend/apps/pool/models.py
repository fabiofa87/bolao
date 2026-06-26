from datetime import timedelta

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class ScoringRule(models.Model):
    exact_score_points = models.PositiveSmallIntegerField(default=5)
    correct_result_points = models.PositiveSmallIntegerField(default=2)
    wrong_draw_bonus = models.PositiveSmallIntegerField(default=1)
    winner_goals_bonus = models.PositiveSmallIntegerField(default=1)
    lock_minutes = models.PositiveSmallIntegerField(default=5)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "regra de pontuação"
        verbose_name_plural = "regras de pontuação"

    @classmethod
    def current(cls):
        rule, _ = cls.objects.get_or_create(pk=1)
        return rule

    def __str__(self):
        return "Regras do bolão"


class Team(models.Model):
    provider_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=120)
    short_name = models.CharField(max_length=80, blank=True)
    code = models.CharField(max_length=4, blank=True)
    crest_url = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "seleção"
        verbose_name_plural = "seleções"

    def __str__(self):
        return self.short_name or self.name


class Match(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Agendado"
        TIMED = "TIMED", "Confirmado"
        IN_PLAY = "IN_PLAY", "Em andamento"
        PAUSED = "PAUSED", "Intervalo"
        FINISHED = "FINISHED", "Finalizado"
        POSTPONED = "POSTPONED", "Adiado"
        CANCELLED = "CANCELLED", "Cancelado"

    provider_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    stage = models.CharField("fase", max_length=40)
    group = models.CharField("grupo", max_length=20, blank=True)
    matchday = models.PositiveSmallIntegerField("rodada", null=True, blank=True)
    kickoff_at = models.DateTimeField("início")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    home_team = models.ForeignKey(
        Team, on_delete=models.PROTECT, related_name="home_matches"
    )
    away_team = models.ForeignKey(
        Team, on_delete=models.PROTECT, related_name="away_matches"
    )
    regular_home = models.PositiveSmallIntegerField(null=True, blank=True)
    regular_away = models.PositiveSmallIntegerField(null=True, blank=True)
    extra_home = models.PositiveSmallIntegerField(null=True, blank=True)
    extra_away = models.PositiveSmallIntegerField(null=True, blank=True)
    penalties_home = models.PositiveSmallIntegerField(null=True, blank=True)
    penalties_away = models.PositiveSmallIntegerField(null=True, blank=True)
    scoring_home = models.PositiveSmallIntegerField(null=True, blank=True)
    scoring_away = models.PositiveSmallIntegerField(null=True, blank=True)
    manual_override = models.BooleanField("ajuste manual", default=False)
    provider_updated_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["kickoff_at", "id"]
        verbose_name = "partida"
        verbose_name_plural = "partidas"

    @property
    def lock_at(self):
        return self.kickoff_at - timedelta(minutes=ScoringRule.current().lock_minutes)

    @property
    def is_locked(self):
        return timezone.now() >= self.lock_at

    @property
    def has_result(self):
        return self.scoring_home is not None and self.scoring_away is not None

    def __str__(self):
        return f"{self.home_team} x {self.away_team}"


class Prediction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="predictions"
    )
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="predictions")
    home_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(0)])
    away_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(0)])
    points = models.PositiveSmallIntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "match"], name="unique_prediction_per_match"
            )
        ]
        ordering = ["match__kickoff_at"]
        verbose_name = "palpite"
        verbose_name_plural = "palpites"

    def __str__(self):
        return f"{self.user}: {self.match} ({self.home_score}x{self.away_score})"


class PredictionRevision(models.Model):
    prediction = models.ForeignKey(
        Prediction, on_delete=models.CASCADE, related_name="revisions"
    )
    home_score = models.PositiveSmallIntegerField()
    away_score = models.PositiveSmallIntegerField()
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="prediction_revisions",
    )

    class Meta:
        ordering = ["-changed_at"]
        verbose_name = "histórico de palpite"
        verbose_name_plural = "históricos de palpites"


class PointAdjustment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="point_adjustments"
    )
    points = models.IntegerField()
    exact_hits = models.IntegerField(default=0)
    reason = models.CharField(max_length=255)
    import_key = models.CharField(max_length=180, blank=True, unique=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_adjustments",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "ajuste de pontuação"
        verbose_name_plural = "ajustes de pontuação"


class SyncRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "RUNNING", "Executando"
        SUCCESS = "SUCCESS", "Sucesso"
        FAILED = "FAILED", "Falhou"

    status = models.CharField(max_length=10, choices=Status.choices)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    matches_received = models.PositiveIntegerField(default=0)
    matches_changed = models.PositiveIntegerField(default=0)
    response_snapshot = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "sincronização"
        verbose_name_plural = "sincronizações"
