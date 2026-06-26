from django.urls import path

from .views import (
    ActivateInviteView,
    DailyChatView,
    InviteInfoView,
    LoginView,
    LogoutView,
    MatchDetailView,
    MatchListView,
    PredictionView,
    ProfileView,
    RankingView,
    SessionView,
)

urlpatterns = [
    path("auth/session/", SessionView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("auth/invite/", InviteInfoView.as_view()),
    path("auth/activate/", ActivateInviteView.as_view()),
    path("profile/", ProfileView.as_view()),
    path("chat/", DailyChatView.as_view()),
    path("matches/", MatchListView.as_view()),
    path("matches/<int:match_id>/", MatchDetailView.as_view()),
    path("matches/<int:match_id>/prediction/", PredictionView.as_view()),
    path("ranking/", RankingView.as_view()),
]
