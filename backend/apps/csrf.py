from django.core import signing
from django.middleware.csrf import get_token

CSRF_SIGNING_SALT = "bolao.api.csrf"
CSRF_MAX_AGE_SECONDS = 60 * 60 * 24


def signed_csrf_token(request):
    return signing.dumps(get_token(request), salt=CSRF_SIGNING_SALT)


def api_csrf_is_valid(request):
    token = request.headers.get("X-CSRFToken", "")
    if not token:
        return False
    try:
        signing.loads(
            token,
            salt=CSRF_SIGNING_SALT,
            max_age=CSRF_MAX_AGE_SECONDS,
        )
        return True
    except signing.BadSignature:
        return False

