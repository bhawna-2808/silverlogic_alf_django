from .dev import *  # noqa

DEFAULT_FILE_STORAGE = "inmemorystorage.InMemoryStorage"

# Emails
DJMAIL_REAL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Speeds up tests.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

ENVIRONMENT = "test"
