from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .accounts.models import Invite
from .pool.models import Match
from .pool.services import build_ranking, save_prediction
from .serializers import (
    InviteActivationSerializer,
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


@method_decorator(ensure_csrf_cookie, name="dispatch")
class SessionView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(
            {
                "authenticated": request.user.is_authenticated,
                "user": UserSerializer(request.user).data
                if request.user.is_authenticated
                else None,
            }
        )


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
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
                {"detail": "E-mail ou senha inválidos."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cache.delete(key)
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(csrf_protect, name="dispatch")
class ActivateInviteView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = InviteActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invite = (
            Invite.objects.select_for_update()
            .filter(token_hash=Invite.hash_token(serializer.validated_data["token"]))
            .first()
        )
        if not invite or not invite.is_valid:
            return Response(
                {"detail": "Convite inválido ou expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user, _ = User.objects.get_or_create(
            email=invite.email,
            defaults={
                "username": invite.email,
                "display_name": invite.display_name,
            },
        )
        user.display_name = serializer.validated_data.get(
            "display_name", invite.display_name
        )
        user.is_active = True
        user.set_password(serializer.validated_data["password"])
        user.save()
        invite.used_at = timezone.now()
        invite.save(update_fields=["used_at"])
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MatchListView(APIView):
    def get(self, request):
        queryset = Match.objects.select_related("home_team", "away_team").prefetch_related(
            "predictions__user"
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
                "predictions__user"
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
        return Response(build_ranking())


class ProfileView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)
