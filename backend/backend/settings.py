import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from django.core.management.utils import get_random_secret_key
from import_export.formats.base_formats import XLSX
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    secret_key: str = get_random_secret_key()
    debug: bool = False
    sqlite: bool = False
    allowed_hosts: str = '127.0.0.1, localhost'
    telegram_token: str
    vk_token: str
    vk_group_id: int
    database_name: str = 'db'
    postgres_user: str = 'user'
    postgres_password: str = 'password'
    db_host: str = 'localhost'
    db_port: int = 5432

    class Config:
        env_file = BASE_DIR.parent / '.env'


settings = Settings()

SECRET_KEY = settings.secret_key

DEBUG = settings.debug

ALLOWED_HOSTS = settings.allowed_hosts.split(', ')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_object_actions',
    'import_export',

    'core.apps.CoreConfig',
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

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

if settings.sqlite:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': settings.database_name,
            'USER': settings.postgres_user,
            'PASSWORD': settings.postgres_password,
            'HOST': settings.db_host,
            'PORT': settings.db_port,
        }
    }

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

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = False

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / STATIC_URL
FILES_URL = 'files/'
FILES_ROOT = BASE_DIR / FILES_URL

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EXPORT_FORMATS = [XLSX]

AUTH_USER_MODEL = 'core.AdminUser'

LOG_DIR = 'logs/'
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILENAME = f'{LOG_DIR}{{platform}}.log'
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(funcName)s:%(lineno)d %(message)s'
LOG_FILE_SIZE = 1024 * 1024
LOG_FILE_COUNT = 5


def get_logger(platform):
    logging.basicConfig(
        level=logging.ERROR,
        format=LOG_FORMAT,
        handlers=[
            RotatingFileHandler(
                filename=LOG_FILENAME.format(platform=platform),
                maxBytes=LOG_FILE_SIZE,
                backupCount=LOG_FILE_COUNT,
            ),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(platform)
