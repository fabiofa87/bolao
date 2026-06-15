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
            raise ValueError("O e-mail é obrigatório.")
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
            raise ValueError("Superusuário precisa de is_staff e is_superuser.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField("e-mail", unique=True)
    display_name = models.CharField("nome", max_length=150)
    username = models.CharField(max_length=150, blank=True)
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
    email = models.EmailField("e-mail")
    display_name = models.CharField("nome", max_length=150)
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    expires_at = models.DateTimeField("expira em")
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
    def issue(cls, *, email, display_name, created_by, valid_days=7):
        raw_token = secrets.token_urlsafe(32)
        invite = cls.objects.create(
            email=email.lower().strip(),
            display_name=display_name.strip(),
            token_hash=cls.hash_token(raw_token),
            expires_at=timezone.now() + timedelta(days=valid_days),
            created_by=created_by,
        )
        return invite, raw_token

    @property
    def is_valid(self):
        return self.used_at is None and self.expires_at > timezone.now()

    def __str__(self):
        return f"{self.display_name} <{self.email}>"

