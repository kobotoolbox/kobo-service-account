import re
import time

import fakeredis
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test.utils import override_settings as dj_override_settings
from mock import patch
from rest_framework.exceptions import AuthenticationFailed

from kobo_service_account.authentication import ServiceAccountAuthentication
from kobo_service_account.exceptions import HostNotAllowedException
from kobo_service_account.models import ServiceAccountUser
from kobo_service_account.settings import DEFAULTS, service_account_settings
from kobo_service_account.utils import get_real_user, get_request_headers


class FakeRequest:
    """
    Mock class to simulate `rest_framework.request.Request`.
    It avoids creating DRF API only to test authentication and
    request headers

    NB: `user` is always `ServiceAccountUser()`
    """

    user = ServiceAccountUser()

    def __init__(self, with_auth: bool, username: str, wrong_auth: bool = False):
        self._with_auth = with_auth
        self._wrong_auth = wrong_auth
        self._username = username

    @property
    def META(self):  # noqa

        meta = {}
        for header_key, header_value in self.headers.items():
            meta[f"HTTP_{header_key.upper().replace('-', '_')}"] = header_value

        return meta

    @property
    def headers(self):
        headers = {'host': 'testserver'}  # Useful to test authentication with host

        if self._with_auth:
            headers.update(get_request_headers(self._username))
            if self._wrong_auth:
                headers['Authorization'] += '-wrong-auth'

        return headers


def test_privileges():
    """
    Simple test to validate class properties
    """
    service_account_user = ServiceAccountUser()
    assert service_account_user.is_superuser
    assert not service_account_user.is_anonymous
    assert service_account_user.is_authenticated


def test_settings():
    """
    Test if Django is reading the correct setting values
    """
    assert hasattr(settings, 'SERVICE_ACCOUNT')
    # Test default values
    assert (
            settings.SERVICE_ACCOUNT['NAMESPACE']
            == DEFAULTS['NAMESPACE']
    )
    assert (
            settings.SERVICE_ACCOUNT['ON_BEHALF_HEADER']
            == DEFAULTS['ON_BEHALF_HEADER']
    )

    # Three values are overridden in pytest
    # Django settings
    assert (
        settings.SERVICE_ACCOUNT['TOKEN_TTL']
        == pytest.test_settings['TOKEN_TTL']
    )
    assert (
        settings.SERVICE_ACCOUNT['TOKEN_TTL_EXPIRY_THRESHOLD']
        == pytest.test_settings['TOKEN_TTL_EXPIRY_THRESHOLD']
    )
    assert (
        settings.SERVICE_ACCOUNT['TOKEN_LENGTH']
        == pytest.test_settings['TOKEN_LENGTH']
    )

    # kobo-service-account settings
    assert (
        service_account_settings.TOKEN_TTL
        == pytest.test_settings['TOKEN_TTL']
    )
    assert (
        service_account_settings.TOKEN_TTL_EXPIRY_THRESHOLD
        == pytest.test_settings['TOKEN_TTL_EXPIRY_THRESHOLD']
    )
    assert (
        service_account_settings.TOKEN_LENGTH
        == pytest.test_settings['TOKEN_LENGTH']
    )


@patch('kobo_service_account.models.ServiceAccountUser.redis_client',
       fakeredis.FakeStrictRedis())
def test_get_existing_authentication_token():
    """
    Test if a new token is not created if the current is still valid
    """
    service_account_user = ServiceAccountUser()
    auth_token = 'my-authentication-token'
    ttl = settings.SERVICE_ACCOUNT['TOKEN_TTL']
    redis_client = service_account_user.redis_client
    assert redis_client.get(ServiceAccountUser.redis_key) is None
    redis_client.setex(ServiceAccountUser.redis_key, ttl, auth_token)
    assert service_account_user.get_or_create_authentication_token() == auth_token


@patch('kobo_service_account.models.ServiceAccountUser.redis_client',
       fakeredis.FakeStrictRedis())
def test_token_rotation():
    """
    Test if a token is regenerated if the current one is about to expire,
    and if the current one is still valid until the time of its TTL.
    """
    service_account_user = ServiceAccountUser()
    ttl = settings.SERVICE_ACCOUNT['TOKEN_TTL']
    threshold = settings.SERVICE_ACCOUNT['TOKEN_TTL_EXPIRY_THRESHOLD']
    redis_client = service_account_user.redis_client

    assert redis_client.get(ServiceAccountUser.redis_key) is None
    auth_token = service_account_user.get_or_create_authentication_token()

    assert redis_client.get(ServiceAccountUser.redis_obsolete_key) is None
    time.sleep(ttl - threshold + 0.5)  # Wait for token expiry
    new_token = service_account_user.get_or_create_authentication_token()
    obsolete_token = redis_client.get(ServiceAccountUser.redis_obsolete_key).decode()
    assert new_token != auth_token
    assert obsolete_token == auth_token

    # validate obsolete_token is valid and ttl is below threshold
    assert service_account_user.has_valid_authentication_token(obsolete_token)
    assert redis_client.ttl(ServiceAccountUser.redis_obsolete_key) <= threshold


@patch('kobo_service_account.models.ServiceAccountUser.redis_client',
       fakeredis.FakeStrictRedis())
@pytest.mark.django_db
def test_get_real_user():
    """
    Test if we can retrieve the real user from request headers
    """
    user = get_user_model().objects.create(username='foo')
    request = FakeRequest(with_auth=True, username=user.username)
    real_user = get_real_user(request)
    assert user == real_user


@patch('kobo_service_account.models.ServiceAccountUser.redis_client',
       fakeredis.FakeStrictRedis())
def test_authentication_success():
    """
    Test if authentication is successful with correct headers
    """
    request = FakeRequest(with_auth=True, username='foo')
    auth_class = ServiceAccountAuthentication()
    auth_user, auth_token = auth_class.authenticate(request)
    assert isinstance(auth_user, ServiceAccountUser)


@patch('kobo_service_account.models.ServiceAccountUser.redis_client',
       fakeredis.FakeStrictRedis())
def test_authentication_failure():
    """
    Test if authentication fails with wrong headers
    """
    request = FakeRequest(with_auth=False, username='foo')
    auth_class = ServiceAccountAuthentication()
    # No authentication to proceed, DRF will try other ones if any
    assert auth_class.authenticate(request) is None

    # Wrong token in header, authentication should failed
    request = FakeRequest(with_auth=True, username='foo', wrong_auth=True)
    with pytest.raises(AuthenticationFailed) as e:
        auth_class.authenticate(request)


def test_authentication_success_with_whitelisted_hosts(override_settings):
    """
    Test if authentication is still successful when a host is whitelisted and
    matches request HTTP_HOST header
    """
    override_settings(WHITELISTED_HOSTS=['testserver'])
    test_authentication_success()


def test_authentication_failure_with_whitelisted_hosts(override_settings):
    """
    Test if authentication fails when a host is whitelisted and does not
    match request HTTP_HOST header
    """
    override_settings(WHITELISTED_HOSTS=['fakeserver'])
    with pytest.raises(HostNotAllowedException) as e:
        test_authentication_success()
