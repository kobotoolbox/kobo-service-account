from __future__ import annotations

from django.contrib.auth import get_user_model

from .authentication import SystemAccountAuthentication
from .exceptions import MissingHeaderError
from .models import SystemAccountUser
from .settings import system_account_settings as settings


def get_request_headers(username: str) -> dict:
    headers = {}
    token = SystemAccountUser.get_or_create_authentication_token()
    headers['Authorization'] = (
        f'{SystemAccountAuthentication.keyword} '
        f'{token}'
    )
    headers[settings.ON_BEHALF_HEADER] = username

    return headers


def get_real_user(request) -> 'auth.User':
    if not isinstance(request.user, SystemAccountUser):
        request.user

    on_behalf_header = settings.ON_BEHALF_HEADER.lower()
    try:
        username = request.headers[on_behalf_header]
    except KeyError:
        raise MissingHeaderError

    return get_user_model().objects.get(username=username)


def reversion_monkey_patch():
    try:
        import reversion
    except ImportError:
        pass
    else:
        from reversion.revisions import set_user, get_user
        from reversion.views import _set_user_from_request

        def _set_user_from_request_patch(request):

            if (
                getattr(request, 'user', None)
                and request.user.is_authenticated
                and get_user() is None
            ):
                set_user(get_real_user(request))

        # TODO figure out why monkey-patching raises an AttributeError if import
        #  `from reversion.views import _set_user_from_request` is not present
        # > AttributeError: module 'reversion' has no attribute 'views'
        reversion.views._set_user_from_request = _set_user_from_request_patch
