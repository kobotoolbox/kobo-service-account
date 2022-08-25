from copy import deepcopy

import pytest
from django.conf import settings
from kobo_service_account.settings import DEFAULTS, service_account_settings


def pytest_configure():
    installed_apps = [
        'django.contrib.contenttypes',
        'django.contrib.auth',
    ]

    # Update some settings for testing purposes.
    pytest.overridden_settings = {
        'TOKEN_TTL': 3,
        'TOKEN_TTL_EXPIRY_THRESHOLD': 2,
        'TOKEN_LENGTH': 10,
    }
    test_settings = deepcopy(DEFAULTS)
    test_settings.update(pytest.overridden_settings)

    settings.configure(
        INSTALLED_APPS=installed_apps,
        SERVICE_ACCOUNT=test_settings,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3'}},
    )
