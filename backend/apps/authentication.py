from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied

from .csrf import api_csrf_is_valid


class SignedCsrfSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return
        if api_csrf_is_valid(request):
            return
        raise PermissionDenied("Token CSRF invalido ou ausente.")

