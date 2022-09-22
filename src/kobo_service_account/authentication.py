from __future__ import annotations

from django.contrib.auth.models import User
from django.core.exceptions import BadRequest
from django.utils.translation import gettext_lazy as t
from rest_framework import HTTP_HEADER_ENCODING, exceptions
from rest_framework.authentication import (
    BaseAuthentication,
    get_authorization_header,
)
from rest_framework.request import Request

from .exceptions import HostNotAllowedException
from .models import ServiceAccountUser
from .settings import service_account_settings as settings


class ServiceAccountAuthentication(BaseAuthentication):
    """
    Token based authentication based on DRF TokenAuthentication.
    Use redis as the backend

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "ServiceAccountToken ".

    For example:

        Authorization: ServiceAccountToken 401f7ac837da42b97f613d789819ff93537bee6a
    """

    keyword = 'ServiceAccountToken'

    def authenticate(self, request: Request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1:
            msg = t('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = t('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = t(
                'Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(token, request)

    def authenticate_credentials(
        self, token: str, request: Request
    ) -> tuple[User, str]:
        service_account_user = ServiceAccountUser()
        if not service_account_user.has_valid_authentication_token(token):
            raise exceptions.AuthenticationFailed(t('Invalid token header.'))

        if settings.WHITELISTED_HOSTS:
            try:
                http_host = request.META['HTTP_HOST']
            except KeyError:
                raise BadRequest

            if http_host not in settings.WHITELISTED_HOSTS:
                raise HostNotAllowedException

        return service_account_user, token

    def authenticate_header(self, request: Request):
        return self.keyword
