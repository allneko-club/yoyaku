from pathlib import Path

from django.conf.global_settings import DATE_INPUT_FORMATS

BASE_DIR = Path(__file__).parent.parent.parent.parent
PROJECT_DIR = BASE_DIR / 'yoyaku'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-%1d8tvxyxs_3@6v8la1)yeo=nujm66^w(kel(-pr1-1z1iw$ns'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'yoyaku.lp',
    'yoyaku.accounts',
    'yoyaku.mail',
    'yoyaku.booking',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'yoyaku.config.urls'

AUTH_USER_MODEL = 'accounts.User'
LOGIN_REDIRECT_URL = 'accounts:顧客一覧'
LOGOUT_REDIRECT_URL = 'authentication:login'
LOGIN_URL = 'authentication:login'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(BASE_DIR / 'yoyaku/core/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'yoyaku.core.templates.context_processors.settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'yoyaku.config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'ja'

TIME_ZONE = 'Asia/Tokyo'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# 日付の入力形式を日本風に対応させる
DATE_INPUT_FORMATS += ('%Y/%m/%d',)

# Static files (CSS, JavaScript, Images)
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = [str(PROJECT_DIR / 'core/static')]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

LOGGING = {
    'disable_existing_loggers': False,
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': '127.0.0.1:11211',
    }
}


AUTH_USER_IDS = (1,)

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

HOSTNAME = ''
YOYAKU_ADMIN_PATH = 'yoyaku-admin'
SITE_NAME = 'YOYAKU'

# 一覧に表示するレコード数の切り替えリスト
PER_PAGE_SET = (25, 50, 100)

# 表示日数
DISP_DAYS = 14

# 受付時間 09:00 ~ 22:00
START_TIME = '09:00'
END_TIME = '22:00'
