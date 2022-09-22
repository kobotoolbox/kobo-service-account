# Kobo Service Account 

This library provides a user with super privileges that allow requests between
KoboToolbox apps regardless of the permissions of user who has initiated the call.  

It uses Redis as the back end for authentication and token persistence. 


## Supported versions

- Python 3.8, 3.9, 3.10
- Django 3.2
- Django REST Framework 3.10

## Quick start

1. Install the package using pip:

```
pip install -e git+https://github.com/kobotoolbox/kobo-service-account.git@a930fa001fc062b076d5e4ee12fe2743f1a76b47#egg=kobo-service-account
```

2. Authenticate your requests with `get_request_headers()` utility

```python
from kobo_service_account.utils import get_request_headers
...

   request = requests.Request(**kwargs)
   request.headers.update(get_request_headers(username))
```

3. Add authentication class to Django Rest Framework authentication class list in your settings:

```python
REST_FRAMEWORK = {
    ...
    'DEFAULT_AUTHENTICATION_CLASSES': (
        ...
        'rest_framework.authentication.SessionAuthentication',
        'kobo_service_account.authentication.ServiceAccountAuthentication',
    ),
}
```

4. Retrieve the user with `get_real_user()` utility

```python
    print(request.user)  # ServiceAccountUser
    print(get_real_user(request.user))  # User 
```


## Django settings

```json
{
    "BACKEND": {
        "LOCATION": "redis://localhost/"
    },
    "NAMESPACE": "kobo-service-account",
    "TOKEN_TTL": 60,
    "TOKEN_TTL_EXPIRY_THRESHOLD": 5,
    "TOKEN_LENGTH": 50,
    "ON_BEHALF_HEADER": "Kobo-Service-Account-On-Behalf",
    "WHITELISTED_HOSTS": [],
}
```

| Variable  | Description |
| ------------- | ------------- |
| `BACKEND`  | Expect a `django-environ` `cache_url` dictionary  |
| `NAMESPACE` | Namespace used to prefix all keys used in redis by this library |
| `TOKEN_TTL` | Token time to live (in seconds) |
| `TOKEN_TTL_EXPIRY_THRESHOLD` | Number of seconds before expiry to generate a new token |
| `TOKEN_LENGTH` | Number of characters of the token |
| `ON_BEHALF_HEADER` | Header name used to pass the real username |
| `WHITELISTED_HOSTS` | Optional. List of hosts which are allowed to use service account authentication headers |

## Test
1. Create a virtual env
2. Install dependencies

```
pip install -r dev_requirements.txt
```
3. Run tests
```
pytest -vv
```
