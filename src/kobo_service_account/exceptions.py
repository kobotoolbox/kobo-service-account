from django.utils.translation import gettext_lazy as t
from rest_framework.exceptions import PermissionDenied


class HostNotAllowedException(PermissionDenied):
    # Similar to django.core.exception.DisallowedHost but extends DRF.APIException
    default_detail = t('Host is not allowed')


class MissingHeaderError(Exception):
    pass
