from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import render
from django.urls import path
from django.utils.text import slugify

from .models import DailyChatMessage, Invite, PoolGroup, User


@admin.register(PoolGroup)
class PoolGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ["email"]
    list_display = ["email", "display_name", "is_active", "is_staff"]
    search_fields = ["email", "display_name"]
    filter_horizontal = ["groups", "user_permissions", "pool_groups"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Perfil", {"fields": ("display_name", "pool_groups")}),
        (
            "Permissoes",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Datas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "display_name",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "pool_groups",
                ),
            },
        ),
    )


class InviteIssueForm(forms.Form):
    kind = forms.ChoiceField(
        label="Tipo",
        choices=Invite.Kind.choices,
        initial=Invite.Kind.SHARED,
    )
    pool_group = forms.ModelChoiceField(
        label="Grupo existente",
        queryset=PoolGroup.objects.filter(is_active=True),
        required=False,
    )
    group_name = forms.CharField(
        label="Criar grupo",
        max_length=120,
        required=False,
        help_text="Opcional. Se preenchido, cria um novo grupo para este convite.",
    )
    display_name = forms.CharField(label="Nome", max_length=150, required=False)
    email = forms.EmailField(label="E-mail", required=False)
    max_uses = forms.IntegerField(
        label="Limite de usos",
        min_value=1,
        required=False,
        help_text="Opcional para convite compartilhado.",
    )
    valid_days = forms.IntegerField(label="Validade em dias", min_value=1, initial=7)

    def clean(self):
        cleaned = super().clean()
        kind = cleaned.get("kind")
        if kind == Invite.Kind.INDIVIDUAL and not (
            cleaned.get("display_name") and cleaned.get("email")
        ):
            raise forms.ValidationError("Convite individual precisa de nome e e-mail.")
        if kind == Invite.Kind.SHARED and not (
            cleaned.get("pool_group") or cleaned.get("group_name")
        ):
            raise forms.ValidationError(
                "Convite compartilhado precisa de um grupo existente ou novo."
            )
        return cleaned


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = [
        "kind",
        "pool_group",
        "display_name",
        "email",
        "used_count",
        "max_uses",
        "expires_at",
        "used_at",
        "created_by",
    ]
    list_filter = ["kind", "pool_group"]
    search_fields = ["display_name", "email", "pool_group__name"]
    readonly_fields = [
        "token_hash",
        "created_at",
        "created_by",
        "used_count",
        "used_at",
    ]
    change_list_template = "admin/accounts/invite/change_list.html"

    def get_urls(self):
        return [
            path("emitir/", self.admin_site.admin_view(self.issue_view), name="issue_invite")
        ] + super().get_urls()

    def has_add_permission(self, request):
        return False

    def issue_view(self, request):
        form = InviteIssueForm(request.POST or None)
        invite_url = None
        if request.method == "POST" and form.is_valid():
            _, token = Invite.issue(
                kind=form.cleaned_data["kind"],
                pool_group=self._resolve_pool_group(form),
                email=form.cleaned_data["email"],
                display_name=form.cleaned_data["display_name"],
                created_by=request.user,
                max_uses=form.cleaned_data["max_uses"],
                valid_days=form.cleaned_data["valid_days"],
            )
            invite_url = f"{settings.FRONTEND_URL}/ativar?token={token}"
            messages.success(request, "Convite criado. O link e exibido apenas agora.")
            form = InviteIssueForm()
        return render(
            request,
            "admin/accounts/invite/issue.html",
            {
                **self.admin_site.each_context(request),
                "title": "Emitir convite",
                "form": form,
                "invite_url": invite_url,
                "opts": self.model._meta,
            },
        )

    def _resolve_pool_group(self, form):
        group_name = form.cleaned_data.get("group_name")
        if group_name:
            group, _ = PoolGroup.objects.get_or_create(
                slug=slugify(group_name),
                defaults={"name": group_name},
            )
            return group
        return form.cleaned_data.get("pool_group")


@admin.register(DailyChatMessage)
class DailyChatMessageAdmin(admin.ModelAdmin):
    list_display = ["pool_group", "user", "chat_date", "created_at", "short_body"]
    list_filter = ["pool_group", "chat_date"]
    search_fields = ["body", "user__display_name", "user__email", "pool_group__name"]
    readonly_fields = ["created_at"]

    @admin.display(description="Mensagem")
    def short_body(self, obj):
        return obj.body[:80]
