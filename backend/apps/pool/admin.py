import json

from django import forms
from django.contrib import admin, messages
from django.core import signing
from django.shortcuts import redirect, render
from django.urls import path, reverse

from .models import (
    Match,
    PointAdjustment,
    ScoringRule,
    SyncRun,
    Team,
)
from .services import ImportRow, import_initial_scores, parse_initial_scores, recalculate_points


@admin.register(ScoringRule)
class ScoringRuleAdmin(admin.ModelAdmin):
    list_display = [
        "exact_score_points",
        "correct_result_points",
        "wrong_draw_bonus",
        "winner_goals_bonus",
        "lock_minutes",
        "updated_at",
    ]

    def has_add_permission(self, request):
        return not ScoringRule.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.pk = 1
        super().save_model(request, obj, form, change)
        recalculate_points()


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "short_name", "code", "provider_id"]
    search_fields = ["name", "short_name", "code"]


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = [
        "kickoff_at",
        "home_team",
        "away_team",
        "stage",
        "status",
        "score",
        "manual_override",
    ]
    list_filter = ["stage", "status", "manual_override"]
    search_fields = ["home_team__name", "away_team__name"]
    autocomplete_fields = ["home_team", "away_team"]

    @admin.display(description="Placar")
    def score(self, obj):
        if not obj.has_result:
            return "-"
        return f"{obj.scoring_home} x {obj.scoring_away}"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        recalculate_points(obj)


class CsvImportForm(forms.Form):
    csv_file = forms.FileField(label="Arquivo CSV")


@admin.register(PointAdjustment)
class PointAdjustmentAdmin(admin.ModelAdmin):
    list_display = ["user", "points", "reason", "created_by", "created_at"]
    search_fields = ["user__display_name", "user__email", "reason"]
    readonly_fields = ["created_at", "created_by", "import_key"]
    change_list_template = "admin/pool/pointadjustment/change_list.html"

    def get_urls(self):
        return [
            path(
                "importar/",
                self.admin_site.admin_view(self.import_view),
                name="import_initial_scores",
            )
        ] + super().get_urls()

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def import_view(self, request):
        rows = None
        signed_rows = None
        form = CsvImportForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and request.POST.get("confirm"):
            try:
                raw_rows = signing.loads(request.POST["payload"], max_age=1800)
                rows = [ImportRow(**row) for row in raw_rows]
                count = import_initial_scores(rows, created_by=request.user)
                messages.success(request, f"{count} participantes importados.")
                return redirect(reverse("admin:pool_pointadjustment_changelist"))
            except (signing.BadSignature, ValueError) as exc:
                messages.error(request, str(exc))
        elif request.method == "POST" and form.is_valid():
            try:
                rows = parse_initial_scores(form.cleaned_data["csv_file"].read())
                signed_rows = signing.dumps([row.__dict__ for row in rows])
            except (UnicodeDecodeError, ValueError) as exc:
                messages.error(request, str(exc))
        return render(
            request,
            "admin/pool/pointadjustment/import.html",
            {
                **self.admin_site.each_context(request),
                "title": "Importar pontuação inicial",
                "form": form,
                "rows": rows,
                "payload": signed_rows,
                "opts": self.model._meta,
            },
        )


@admin.register(SyncRun)
class SyncRunAdmin(admin.ModelAdmin):
    list_display = [
        "started_at",
        "status",
        "matches_received",
        "matches_changed",
        "finished_at",
    ]
    readonly_fields = [
        "status",
        "started_at",
        "finished_at",
        "matches_received",
        "matches_changed",
        "response_snapshot",
        "error",
    ]

    def has_add_permission(self, request):
        return False
