from django.utils.translation import gettext_lazy as t
from rest_framework import HTTP_HEADER_ENCODING, exceptions
from rest_framework.authentication import BaseAuthentication

from .models import SystemAccountUser


class SystemAccountAuthentication(BaseAuthentication):
    """
    Token based authentication based on DRF TokenAuthentication.
    Use redis as the backend

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "SystemAccountToken ".

    For example:

        Authorization: SystemAccountToken 401f7ac837da42b97f613d789819ff93537bee6a
    """

    keyword = 'SystemAccountToken'

    def authenticate(self, request):
        auth = self.get_authorization_header(request).split()

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

    def authenticate_credentials(self, key, request):
        system_account_user = SystemAccountUser()
        if not system_account_user.has_valid_authentication_token(key):
            raise exceptions.AuthenticationFailed(t('Invalid token header.'))

        return system_account_user, key

    def authenticate_header(self, request):
        return self.keyword

    @staticmethod
    def get_authorization_header(request):
        auth = request.META.get('HTTP_AUTHORIZATION', b'')
        if isinstance(auth, str):
            # Work around django test client oddness
            auth = auth.encode(HTTP_HEADER_ENCODING)
        return auth
