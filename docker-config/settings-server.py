import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "wz$ns1s)!r58z)dn1tub(@-3ifm!l)n_y%mt=*ki(c_cs_e_-0"
PASSWORD_RESET_TIMEOUT_DAYS = 14

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG") == 'True'

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
            ],
        },
    },
]

WSGI_APPLICATION = "twio_web.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PW"),
        "HOST": os.environ.get("DB_HOST"),
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

TO_EMAIL = os.environ.get("TO_EMAIL")
EMAIL_USE_TLS = True
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

AUTHENTICATION_BACKENDS = ["user_handling.backends.EmailBackend"]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# send logs to stdout for Unicorn/Docker
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
    },
    'handlers': {
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
    }
}
