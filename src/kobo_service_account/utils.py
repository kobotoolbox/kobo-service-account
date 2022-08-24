from __future__ import annotations

from typing import Union

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.http import HttpRequest
from rest_framework.request import Request

from .authentication import ServiceAccountAuthentication
from .exceptions import MissingHeaderError
from .models import ServiceAccountUser
from .settings import service_account_settings as settings


def get_real_user(request: Union[Request, HttpRequest]) -> User:
    """
    Return a real Django User object.
    If `request.user` is the sysadmin user, it tries to load the real
    user from the username passed in the request headers with authentication
    token.
    Otherwise, return `request.user` itself.
    """
    if not isinstance(request.user, ServiceAccountUser):
        return request.user

    on_behalf_header = settings.ON_BEHALF_HEADER.lower()
    try:
        username = request.headers[on_behalf_header]
    except KeyError:
        raise MissingHeaderError

    return get_user_model().objects.get(username=username)


def get_request_headers(username: str) -> dict:
    """
    Return a dict to insert in headers to authenticated proxied requests
    Python apps
    """
    headers = {}
    token = ServiceAccountUser.get_or_create_authentication_token()
    headers['Authorization'] = (
        f'{ServiceAccountAuthentication.keyword} '
        f'{token}'
    )
    headers[settings.ON_BEHALF_HEADER] = username

    return headers


def reversion_monkey_patch():
    """
    Reversion always needs a real Django User object. ServiceAccountUser instances
    do not have any representation in the DB, therefore Reversion is not able
    to insert data in DB. This patch fixes it by returning the user for whom
    the sysadmin is making the request.
    """
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
