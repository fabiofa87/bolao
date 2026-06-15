from datetime import datetime

import httpx
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Match, SyncRun, Team
from .services import recalculate_points


def _score_pair(score, key):
    value = score.get(key) or {}
    return value.get("home"), value.get("away")


def extract_scores(score):
    full_home, full_away = _score_pair(score, "fullTime")
    regular_home, regular_away = _score_pair(score, "regularTime")
    extra_home, extra_away = _score_pair(score, "extraTime")
    penalties_home, penalties_away = _score_pair(score, "penalties")

    if full_home is None or full_away is None:
        scoring_home = scoring_away = None
    elif penalties_home is not None and penalties_away is not None:
        scoring_home = max(0, full_home - penalties_home)
        scoring_away = max(0, full_away - penalties_away)
    else:
        scoring_home, scoring_away = full_home, full_away

    if regular_home is None and scoring_home is not None:
        regular_home = max(0, scoring_home - (extra_home or 0))
        regular_away = max(0, scoring_away - (extra_away or 0))

    return {
        "regular_home": regular_home,
        "regular_away": regular_away,
        "extra_home": extra_home,
        "extra_away": extra_away,
        "penalties_home": penalties_home,
        "penalties_away": penalties_away,
        "scoring_home": scoring_home,
        "scoring_away": scoring_away,
    }


def _upsert_team(data, placeholder_name):
    if data.get("id") is None:
        team, _ = Team.objects.get_or_create(
            provider_id=None,
            name=placeholder_name,
            defaults={"short_name": "A definir"},
        )
        return team
    team, _ = Team.objects.update_or_create(
        provider_id=data["id"],
        defaults={
            "name": data.get("name") or data.get("shortName") or "A definir",
            "short_name": data.get("shortName") or "",
            "code": data.get("tla") or "",
            "crest_url": data.get("crest") or "",
        },
    )
    return team


@transaction.atomic
def apply_matches(payload):
    changed = 0
    for item in payload.get("matches", []):
        home = _upsert_team(item["homeTeam"], f"A definir - mandante {item['id']}")
        away = _upsert_team(item["awayTeam"], f"A definir - visitante {item['id']}")
        provider_updated_at = parse_datetime(item.get("lastUpdated", ""))
        defaults = {
            "stage": item.get("stage") or "UNKNOWN",
            "group": item.get("group") or "",
            "matchday": item.get("matchday"),
            "kickoff_at": parse_datetime(item["utcDate"]),
            "status": item.get("status") or Match.Status.SCHEDULED,
            "home_team": home,
            "away_team": away,
            "provider_updated_at": provider_updated_at,
        }
        match, created = Match.objects.get_or_create(
            provider_id=item["id"], defaults=defaults
        )
        if match.manual_override:
            continue
        score_values = extract_scores(item.get("score") or {})
        before = (
            match.kickoff_at,
            match.status,
            match.scoring_home,
            match.scoring_away,
        )
        for field, value in {**defaults, **score_values}.items():
            setattr(match, field, value)
        match.save()
        after = (
            match.kickoff_at,
            match.status,
            match.scoring_home,
            match.scoring_away,
        )
        if created or before != after:
            changed += 1
            recalculate_points(match)
    return changed


def sync_world_cup():
    run = SyncRun.objects.create(status=SyncRun.Status.RUNNING)
    try:
        if not settings.FOOTBALL_DATA_API_TOKEN:
            raise RuntimeError("FOOTBALL_DATA_API_TOKEN não configurado.")
        response = httpx.get(
            f"{settings.FOOTBALL_DATA_BASE_URL}/competitions/WC/matches",
            params={"season": 2026},
            headers={"X-Auth-Token": settings.FOOTBALL_DATA_API_TOKEN},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        changed = apply_matches(payload)
        run.status = SyncRun.Status.SUCCESS
        run.matches_received = len(payload.get("matches", []))
        run.matches_changed = changed
        run.response_snapshot = {
            "resultSet": payload.get("resultSet", {}),
            "filters": payload.get("filters", {}),
        }
        return run
    except Exception as exc:
        run.status = SyncRun.Status.FAILED
        run.error = str(exc)
        raise
    finally:
        run.finished_at = timezone.now()
        run.save()
