from django.contrib.auth import get_user_model
from rest_framework import serializers

from .accounts.models import DailyChatMessage, PoolGroup
from .pool.models import Match, Prediction, Team

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "display_name"]


class PoolGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoolGroup
        fields = ["id", "name", "slug"]


class DailyChatMessageSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.display_name", read_only=True)

    class Meta:
        model = DailyChatMessage
        fields = ["id", "pool_group", "user", "user_name", "body", "chat_date", "created_at"]


class DailyChatMessageInputSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=500, trim_whitespace=True)
    pool_group = serializers.IntegerField(required=False)

    def validate_body(self, value):
        if not value.strip():
            raise serializers.ValidationError("Mensagem vazia.")
        return value.strip()


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "name", "short_name", "code", "crest_url"]


class PredictionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.display_name", read_only=True)

    class Meta:
        model = Prediction
        fields = [
            "id",
            "user",
            "user_name",
            "home_score",
            "away_score",
            "points",
            "submitted_at",
            "updated_at",
        ]


class MatchSerializer(serializers.ModelSerializer):
    home_team = TeamSerializer()
    away_team = TeamSerializer()
    lock_at = serializers.DateTimeField(read_only=True)
    is_locked = serializers.BooleanField(read_only=True)
    my_prediction = serializers.SerializerMethodField()
    predictions = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = [
            "id",
            "provider_id",
            "stage",
            "group",
            "matchday",
            "kickoff_at",
            "lock_at",
            "is_locked",
            "status",
            "home_team",
            "away_team",
            "scoring_home",
            "scoring_away",
            "penalties_home",
            "penalties_away",
            "my_prediction",
            "predictions",
        ]

    def get_my_prediction(self, obj):
        user = self.context["request"].user
        prediction = next((p for p in obj.predictions.all() if p.user_id == user.id), None)
        return PredictionSerializer(prediction).data if prediction else None

    def get_predictions(self, obj):
        return []


class PredictionInputSerializer(serializers.Serializer):
    home_score = serializers.IntegerField(min_value=0, max_value=99)
    away_score = serializers.IntegerField(min_value=0, max_value=99)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)


class InviteActivationSerializer(serializers.Serializer):
    token = serializers.CharField()
    email = serializers.EmailField(required=False)
    password = serializers.CharField(min_length=8, trim_whitespace=False)
    display_name = serializers.CharField(max_length=150, required=False)


class InviteInfoSerializer(serializers.Serializer):
    token = serializers.CharField()
