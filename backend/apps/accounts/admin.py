from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import redirect, render
from django.urls import path, reverse

from .models import Invite, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ["email"]
    list_display = ["email", "display_name", "is_active", "is_staff"]
    search_fields = ["email", "display_name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Perfil", {"fields": ("display_name",)}),
        (
            "Permissões",
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
                ),
            },
        ),
    )


class InviteIssueForm(forms.Form):
    display_name = forms.CharField(label="Nome", max_length=150)
    email = forms.EmailField(label="E-mail")


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ["display_name", "email", "expires_at", "used_at", "created_by"]
    search_fields = ["display_name", "email"]
    readonly_fields = [
        "token_hash",
        "created_at",
        "created_by",
        "used_at",
        "expires_at",
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
                email=form.cleaned_data["email"],
                display_name=form.cleaned_data["display_name"],
                created_by=request.user,
            )
            invite_url = f"{settings.FRONTEND_URL}/ativar?token={token}"
            messages.success(request, "Convite criado. O link é exibido apenas agora.")
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

