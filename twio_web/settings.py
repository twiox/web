import os

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Debug is on by default for local development; production sets DEBUG=False
DEBUG = os.environ.get("DEBUG", "True") == "True"

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG is off")
    SECRET_KEY = "django-insecure-local-development-only"

PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 14  # 14 days

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "members.apps.MembersConfig",
    "interested.apps.InterestedConfig",
    "organizers.apps.OrganizersConfig",
    "trainer.apps.TrainerConfig",
    "user_handling.apps.UserHandlingConfig",
    "six",
    "multiselectfield",
    "compressor",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "twio_web.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "members.roles.roles",
                "members.context_processors.nav_section",
            ],
        },
    },
]

WSGI_APPLICATION = "twio_web.wsgi.application"


# Database
DATABASES = {
   "default": {
       "ENGINE": "django.db.backends.sqlite3",
       "NAME": os.environ.get("SQLITE_PATH") or os.path.join(BASE_DIR, "db.sqlite3"),
       "OPTIONS": {
           # take the write lock at BEGIN, wait for it instead of failing with "database is locked"
           "transaction_mode": "IMMEDIATE",
           "timeout": 20,
           # WAL: readers don't block the writer; NORMAL is safe with WAL
           "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
       },
   },
}

CONN_MAX_AGE = 300

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_L10N = True
USE_TZ = False

# this is used fr SCSS
COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)
COMPRESS_ROOT = os.path.join(BASE_DIR, "static")

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

LOGOUT_REDIRECT_URL = "/login/"
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_ROOT = os.path.join(BASE_DIR, "media")  # where are the files at the file-system?
MEDIA_URL = "/media/"  # how do we access the media in the browser?
# for the login
LOGIN_REDIRECT_URL = "index"
LOGIN_URL = "login"

# Email. Without EMAIL_HOST (local development) emails are printed to the console instead of sent.
TO_EMAIL = os.environ.get("TO_EMAIL", "web@localhost")  # Emails from the user-site are send there
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "webmaster@localhost")
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
if not EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

AUTHENTICATION_BACKENDS = ["user_handling.backends.EmailBackend"]
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# traefik terminates TLS and tells Django the original scheme
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Prod needs all logs in STDOUT, collect by Docker
# Keeps Django's default loggers, so runserver still shows its request log locally.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "handlers": {
        "stdout_errors": {
            "class": "logging.StreamHandler",
            "level": "ERROR",
            "filters": ["require_debug_false"],
        },
    },
    "root": {"handlers": ["stdout_errors"]},
}
