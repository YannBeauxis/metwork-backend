"""
Django settings for metwork project.

Generated by 'django-admin startproject' using Django 1.11.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import sys
from rdkit import RDLogger

with open(os.environ['METWORK_BACKEND_PATH'] + '/VERSION') as f:
	APP_VERSION = f.read().strip()
	
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = os.environ['METWORK_SECRET_KEY']
SECRET_KEY='SECRET_KEY'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Rdkit warnings
#RDLogger.logger().setLevel(RDLogger.ERROR)
RDLogger.logger().setLevel(RDLogger.CRITICAL)

ALLOWED_HOSTS = [os.environ['METWORK_ALLOWED_HOSTS']]

# Application definition

INSTALLED_APPS = [
	'django.contrib.contenttypes',
	'django.contrib.auth',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'polymorphic',
	'django_rdkit',
	'django_extensions',
	'corsheaders',
	'rest_framework',
	'rest_framework.authtoken',
	'django_celery_results',
	'base',
	'metabolization',
	'fragmentation',
	'django.contrib.admin',
]

MIDDLEWARE = [
	'django.middleware.security.SecurityMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'corsheaders.middleware.CorsMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = 'metwork_backend.urls'

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

WSGI_APPLICATION = 'metwork_backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

# => See dev.py and production.py


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

# All settings common to all environments
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

DATA_FILES_PATH = os.environ['METWORK_DATA_FILES_PATH']
APP_CONFIG = os.environ['METWORK_APP_CONFIG']

AUTH_USER_MODEL = 'base.User'

REST_FRAMEWORK = {
	#'DEFAULT_PERMISSION_CLASSES': (
	#   'rest_framework.permissions.AllowAny',
	#),  
	'DEFAULT_AUTHENTICATION_CLASSES': (
		'rest_framework.authentication.TokenAuthentication',
		'rest_framework.authentication.SessionAuthentication',
	),
	'PAGE_SIZE': 100,
	'EXCEPTION_HANDLER': 'rest_framework_json_api.exceptions.exception_handler',
	'DEFAULT_PAGINATION_CLASS':
		'rest_framework_json_api.pagination.PageNumberPagination',
	'DEFAULT_PARSER_CLASSES': (
		'rest_framework_json_api.parsers.JSONParser',
		'rest_framework.parsers.FormParser',
		'rest_framework.parsers.MultiPartParser'
	),
	'DEFAULT_RENDERER_CLASSES': (
		'rest_framework_json_api.renderers.JSONRenderer',
		'rest_framework.renderers.BrowsableAPIRenderer',
	),
	'DEFAULT_METADATA_CLASS': 'rest_framework_json_api.metadata.JSONAPIMetadata',
}

"""
LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'handlers': {
		'console': {
			'class': 'logging.StreamHandler',
		},
	},
	'loggers': {
		'django': {
			'handlers': ['console'],
			'level': 'DEBUG',
		},
	},
}
"""

# Send mail
DEFAULT_FROM_EMAIL = 'metwork@pharmacie.parisdescartes.fr'
SERVER_EMAIL = 'metwork.dev@gmail.com'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'metwork.dev@gmail.com'
EMAIL_HOST_PASSWORD = os.environ['METWORK_EMAIL_HOST_PASSWORD']

# Celery settings

#: Only add pickle to this list if your broker is secured
#: from unwanted access (see userguide/security.html)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_BACKEND = 'django-cache'
CELERY_TASK_SERIALIZER = 'json'
CELERY_TRACK_STARTED = True
CELERY_TASK_DEFAULT_QUEUE = 'default.' + APP_VERSION
CELERY_RUN_QUEUE = 'run.' + APP_VERSION
CELERY_QUEUES = {
	CELERY_TASK_DEFAULT_QUEUE: 
		{"exchange": CELERY_TASK_DEFAULT_QUEUE,
		"routing_key": CELERY_TASK_DEFAULT_QUEUE},
	CELERY_RUN_QUEUE: 
		{"exchange": CELERY_RUN_QUEUE,
		"routing_key": CELERY_RUN_QUEUE}}
			

