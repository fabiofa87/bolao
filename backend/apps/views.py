from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.cache import cache
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .accounts.models import DailyChatMessage, Invite, PoolGroup
from .csrf import api_csrf_is_valid, signed_csrf_token
from .pool.models import Match, Prediction
from .pool.services import build_ranking, save_prediction
from .serializers import (
    InviteActivationSerializer,
    InviteInfoSerializer,
    DailyChatMessageInputSerializer,
    DailyChatMessageSerializer,
    LoginSerializer,
    MatchSerializer,
    PredictionInputSerializer,
    PredictionSerializer,
    UserSerializer,
)

User = get_user_model()


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR", "")


class ApiCsrfMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            if not api_csrf_is_valid(request):
                return JsonResponse(
                    {"detail": "Token CSRF invalido ou ausente."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        return super().dispatch(request, *args, **kwargs)


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


@method_decorator(ensure_csrf_cookie, name="dispatch")
class SessionView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(
            {
                "authenticated": request.user.is_authenticated,
                "csrf_token": signed_csrf_token(request),
                "user": UserSerializer(request.user).data
                if request.user.is_authenticated
                else None,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(ApiCsrfMixin, APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        key = f"login:{_client_ip(request)}:{email}"
        attempts = cache.get(key, 0)
        if attempts >= settings.LOGIN_MAX_ATTEMPTS:
            return Response(
                {"detail": "Muitas tentativas. Aguarde antes de tentar novamente."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        user = authenticate(
            request,
            email=email,
            password=serializer.validated_data["password"],
        )
        if user is None:
            cache.set(key, attempts + 1, settings.LOGIN_LOCK_SECONDS)
            return Response(
                {"detail": "E-mail ou senha invalidos."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cache.delete(key)
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class InviteInfoView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        serializer = InviteInfoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        invite = Invite.objects.filter(
            token_hash=Invite.hash_token(serializer.validated_data["token"])
        ).select_related("pool_group").first()
        if not invite or not invite.is_valid:
            return Response(
                {"detail": "Convite invalido ou expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "kind": invite.kind,
                "is_shared": invite.is_shared,
                "email": "" if invite.is_shared else invite.email,
                "display_name": "" if invite.is_shared else invite.display_name,
                "pool_group": invite.pool_group.name if invite.pool_group else "",
                "remaining_uses": None
                if invite.max_uses is None
                else max(0, invite.max_uses - invite.used_count),
                "expires_at": invite.expires_at,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class ActivateInviteView(ApiCsrfMixin, APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = InviteActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invite = (
            Invite.objects.select_for_update(of=("self",))
            .filter(token_hash=Invite.hash_token(serializer.validated_data["token"]))
            .first()
        )
        if not invite or not invite.is_valid:
            return Response(
                {"detail": "Convite invalido ou expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invite.is_shared:
            email = serializer.validated_data.get("email", "").lower().strip()
            display_name = serializer.validated_data.get("display_name", "").strip()
            if not email or not display_name:
                return Response(
                    {"detail": "Informe nome e e-mail para usar este convite."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            email = invite.email
            display_name = serializer.validated_data.get(
                "display_name", invite.display_name
            )

        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"username": email, "display_name": display_name},
        )
        user.display_name = display_name
        user.is_active = True
        user.set_password(serializer.validated_data["password"])
        user.save()
        pool_group = invite.pool_group
        if pool_group is None:
            pool_group, _ = PoolGroup.objects.get_or_create(
                slug="geral", defaults={"name": "Geral"}
            )
        user.pool_groups.add(pool_group)

        if invite.is_shared:
            invite.used_count += 1
            invite.save(update_fields=["used_count"])
        else:
            invite.used_at = timezone.now()
            invite.used_count = 1
            invite.save(update_fields=["used_at", "used_count"])

        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


def prediction_prefetch_for(request):
    now = timezone.now()
    return Prefetch(
        "predictions",
        queryset=Prediction.objects.select_related("user").filter(
            Q(user=request.user) | Q(match__kickoff_at__lte=now)
        ),
    )


class MatchListView(APIView):
    def get(self, request):
        queryset = Match.objects.select_related("home_team", "away_team").prefetch_related(
            prediction_prefetch_for(request)
        )
        stage = request.query_params.get("stage")
        upcoming = request.query_params.get("upcoming")
        if stage:
            queryset = queryset.filter(stage=stage)
        if upcoming == "1":
            queryset = queryset.filter(kickoff_at__gte=timezone.now())
        return Response(
            MatchSerializer(queryset, many=True, context={"request": request}).data
        )


class MatchDetailView(APIView):
    def get(self, request, match_id):
        match = get_object_or_404(
            Match.objects.select_related("home_team", "away_team").prefetch_related(
                prediction_prefetch_for(request)
            ),
            pk=match_id,
        )
        return Response(MatchSerializer(match, context={"request": request}).data)


class PredictionView(APIView):
    def put(self, request, match_id):
        serializer = PredictionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prediction = save_prediction(
            user=request.user, match_id=match_id, **serializer.validated_data
        )
        return Response(PredictionSerializer(prediction).data)


class RankingView(APIView):
    def get(self, request):
        return Response(build_ranking(request.user))


class ProfileView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class DailyChatView(APIView):
    def get_user_groups(self, request):
        return PoolGroup.objects.filter(users=request.user, is_active=True).order_by("name")

    def get_selected_group(self, request, groups):
        group_id = request.query_params.get("pool_group")
        if group_id:
            return get_object_or_404(groups, pk=group_id)
        return groups.first()

    def get(self, request):
        today = timezone.localdate()
        groups = self.get_user_groups(request)
        group = self.get_selected_group(request, groups)
        if group is None:
            return Response(
                {"groups": [], "selected_group": None, "chat_date": today, "messages": []}
            )
        messages = DailyChatMessage.objects.filter(
            pool_group=group,
            chat_date=today,
        ).select_related("user")
        return Response(
            {
                "groups": [
                    {"id": item.id, "name": item.name, "slug": item.slug}
                    for item in groups
                ],
                "selected_group": {"id": group.id, "name": group.name, "slug": group.slug},
                "chat_date": today,
                "messages": DailyChatMessageSerializer(messages, many=True).data,
            }
        )

    def post(self, request):
        serializer = DailyChatMessageInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        groups = self.get_user_groups(request)
        pool_group_id = serializer.validated_data.get("pool_group")
        if pool_group_id:
            group = get_object_or_404(groups, pk=pool_group_id)
        else:
            group = groups.first()
        if group is None:
            return Response(
                {"detail": "Voce nao pertence a nenhum grupo de bolao."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        message = DailyChatMessage.objects.create(
            pool_group=group,
            user=request.user,
            body=serializer.validated_data["body"],
            chat_date=timezone.localdate(),
        )
        return Response(DailyChatMessageSerializer(message).data, status=status.HTTP_201_CREATED)
