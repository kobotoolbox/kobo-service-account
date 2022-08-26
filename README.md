# Kobo Service Account 

This library provides a user with super privileges with allow requests between
KoboToolbox apps regardless of the permissions of user who has initiated the call.  

It uses Redis as the back end for authentication and token persistence. 


## Supported versions
- Python 3.8, 3.9, 3.10
- Django 3.2
- Django REST Framework 3.10

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
| `WHITELISTED_HOSTS` | Optional. List of hosts authorized to send requests with service account user |
