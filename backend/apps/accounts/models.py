import hashlib
import secrets
from datetime import timedelta

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("O e-mail e obrigatorio.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("Superusuario precisa de is_staff e is_superuser.")
        return self._create_user(email, password, **extra_fields)


class PoolGroup(models.Model):
    name = models.CharField("nome", max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    is_active = models.BooleanField("ativo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "grupo de bolao"
        verbose_name_plural = "grupos de bolao"

    def __str__(self):
        return self.name


class User(AbstractUser):
    email = models.EmailField("e-mail", unique=True)
    display_name = models.CharField("nome", max_length=150)
    username = models.CharField(max_length=150, blank=True)
    pool_groups = models.ManyToManyField(
        PoolGroup,
        blank=True,
        related_name="users",
        verbose_name="grupos de bolao",
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]
    objects = UserManager()

    def save(self, *args, **kwargs):
        self.email = self.email.lower().strip()
        self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name or self.email


class Invite(models.Model):
    class Kind(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL", "Individual"
        SHARED = "SHARED", "Compartilhado"

    kind = models.CharField(
        "tipo", max_length=20, choices=Kind.choices, default=Kind.INDIVIDUAL
    )
    pool_group = models.ForeignKey(
        PoolGroup,
        on_delete=models.PROTECT,
        related_name="invites",
        verbose_name="grupo de bolao",
        null=True,
        blank=True,
    )
    email = models.EmailField("e-mail", blank=True)
    display_name = models.CharField("nome", max_length=150, blank=True)
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    expires_at = models.DateTimeField("expira em")
    max_uses = models.PositiveIntegerField("limite de usos", null=True, blank=True)
    used_count = models.PositiveIntegerField("usos", default=0)
    used_at = models.DateTimeField("usado em", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_invites",
        verbose_name="criado por",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "convite"
        verbose_name_plural = "convites"

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def issue(
        cls,
        *,
        created_by,
        email="",
        display_name="",
        pool_group=None,
        kind=Kind.INDIVIDUAL,
        valid_days=7,
        max_uses=None,
    ):
        raw_token = secrets.token_urlsafe(32)
        invite = cls.objects.create(
            kind=kind,
            pool_group=pool_group,
            email=email.lower().strip(),
            display_name=display_name.strip(),
            token_hash=cls.hash_token(raw_token),
            expires_at=timezone.now() + timedelta(days=valid_days),
            max_uses=max_uses,
            created_by=created_by,
        )
        return invite, raw_token

    @property
    def is_valid(self):
        if self.expires_at <= timezone.now():
            return False
        if self.kind == self.Kind.INDIVIDUAL:
            return self.used_at is None
        return self.max_uses is None or self.used_count < self.max_uses

    @property
    def is_shared(self):
        return self.kind == self.Kind.SHARED

    def __str__(self):
        if self.is_shared:
            return f"Convite compartilhado - {self.pool_group}"
        return f"{self.display_name} <{self.email}>"

