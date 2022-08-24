import redis
from django.contrib.auth.models import (
    _user_get_permissions as user_get_permissions,  # noqa
    Group,
    Permission,
)
from django.db.models.manager import EmptyManager
from django.utils.crypto import get_random_string

from .settings import system_account_settings as settings


class SystemAccountUser:
    """

    """

    id = None
    pk = None
    username = 'system_user'
    is_staff = True
    is_active = True
    is_superuser = True
    _groups = EmptyManager(Group)
    _user_permissions = EmptyManager(Permission)
    redis_client = redis.Redis.from_url(
        settings.BACKEND['LOCATION']
    )
    redis_key = f'{settings.NAMESPACE}::authentication_key::current'
    redis_obsolete_key = f'{settings.NAMESPACE}::authentication_key::obsolete'

    def __str__(self):
        return 'SystemAccountUser'

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __hash__(self):
        # instances always return the same hash value but different from
        # `django.contrib.auth.models.AnonymousUser`
        return 2

    def __int__(self):
        raise TypeError(
            'Cannot cast SystemAccountUser to int. '
            'Are you trying to use it in place of User?'
        )

    def check_password(self, raw_password):
        raise NotImplementedError(
            "Django doesn't provide a DB representation for SystemAccountUser."
        )

    def delete(self):
        raise NotImplementedError(
            "Django doesn't provide a DB representation for SystemAccountUser."
        )

    def get_all_permissions(self, obj=None):
        return user_get_permissions(self, obj, 'all')

    def get_group_permissions(self, obj=None):
        return user_get_permissions(self, obj, 'group')

    @classmethod
    def get_or_create_authentication_token(cls):
        ttl = cls.redis_client.ttl(cls.redis_key)
        if ttl >= settings.TOKEN_TTL_EXPIRY_THRESHOLD:
            token = cls.redis_client.get(cls.redis_key)
            # if `settings.TOKEN_TTL_EXPIRY_THRESHOLD` is (close to) 0,
            # redis.get() could return None.
            if token:
                return token.decode()

        # Rotate keys to avoid race conditions when a new key is created
        # just after a request is sent with old key but before authentication
        # is completed.
        p = cls.redis_client.pipeline()
        # ttl equals -2 when key has expired
        if 0 < ttl < settings.TOKEN_TTL_EXPIRY_THRESHOLD:
            p.rename(cls.redis_key, cls.redis_obsolete_key)
        token = get_random_string(settings.TOKEN_LENGTH)
        p.setex(cls.redis_key, settings.TOKEN_TTL, token)
        p.execute()
        return token

    def get_user_permissions(self, obj=None):
        return user_get_permissions(self, obj, 'user')

    def get_username(self) -> str:
        return self.username

    @property
    def groups(self):
        # This user does not belong to any groups (yet?).
        return self._groups

    def has_module_perms(self, module) -> bool:
        return True

    def has_perm(self, perm, obj=None) -> bool:
        return True

    def has_perms(self, perm_list, obj=None) -> bool:
        return True

    @classmethod
    def has_valid_authentication_token(cls, header_token: str) -> bool:
        """
        Validate whether the token equals the current token or the previous one
        which is about to expire.

        It gives a chance to requests sent with an old token but could not
        authenticated in time before the new token is created.
        """
        redis_token = cls.redis_client.get(cls.redis_key)  # returns bytes
        # If redis returns `None`, even the previous one has expired. No need to
        # go further.
        if not redis_token:
            return False

        # We have a match, return True.
        if redis_token.decode() == header_token:
            return True

        # Last chance, compare with previous token if it exists
        redis_token = cls.redis_client.get(cls.redis_obsolete_key)
        if not redis_token:
            return False

        return redis_token.decode() == header_token

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def is_authenticated(self) -> bool:
        return True

    def save(self):
        raise NotImplementedError(
            "Django doesn't provide a DB representation for SystemAccountUser."
        )

    def set_password(self, raw_password):
        raise NotImplementedError(
            "Django doesn't provide a DB representation for SystemAccountUser."
        )

    @property
    def user_permissions(self):
        # This user does not have any assigned permissions.
        return self._user_permissions
