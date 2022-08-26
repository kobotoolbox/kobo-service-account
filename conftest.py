from copy import deepcopy
from typing import Any

import pytest
from django.conf import settings
from kobo_service_account.settings import DEFAULTS, service_account_settings


def pytest_configure():
    installed_apps = [
        'django.contrib.contenttypes',
        'django.contrib.auth',
    ]

    # Update some settings for testing purposes.
    pytest.test_settings = {
        'TOKEN_TTL': 3,
        'TOKEN_TTL_EXPIRY_THRESHOLD': 2,
        'TOKEN_LENGTH': 10,
    }
    test_settings = deepcopy(DEFAULTS)
    test_settings.update(pytest.test_settings)

    settings.configure(
        INSTALLED_APPS=installed_apps,
        SERVICE_ACCOUNT=test_settings,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3'}},
    )


@pytest.fixture
def override_settings():
    """
    Simple fixture to override kobo-service-account settings during the life of
    a test. Same idea as `django.test.utils.override_settings` but without the
    need to pass the all `SERVICE_ACCOUNT` dictionary
    """
    old_settings = {}

    def _override_settings(**new_settings):
        for setting, new_value in new_settings.items():
            old_settings[setting] = getattr(service_account_settings, setting)
            setattr(service_account_settings, setting, new_value)
        return new_settings

    yield _override_settings

    # TearDown
    for setting, old_value in old_settings.items():
        setattr(service_account_settings, setting, old_value)
