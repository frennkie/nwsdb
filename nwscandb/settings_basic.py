# -*- coding: utf-8 -*-
"""
Django settings for nwscandb project.

Generated by 'django-admin startproject' using Django 1.8.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = None  # set in settings_prod_secret.py

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'django.contrib.humanize',
    'django_python3_ldap',
    'sslserver',
    'sniplates',
    'crispy_forms',
    'reversion',
    'djcelery',
    'accounts',
    'dbimport',
    'nmap',
    'multidns',
    'mptt',
    'rest_framework',
)

LOGIN_URL = '/accounts/login/'
LOGOUT_URL = '/accounts/logout/'
LOGIN_REDIRECT_URL = '/'  # TODO raus?! ändern?

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.PersistentRemoteUserMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_python3_ldap.auth.LDAPBackend',
)

# The URL of the LDAP server.
LDAP_AUTH_URL = "ldap://localhost"

# Initiate TLS on connection.
LDAP_AUTH_USE_TLS = False

# The LDAP search base for looking up users.
LDAP_AUTH_SEARCH_BASE = "ou=users,dc=denm,dc=de"

# The LDAP class that represents a user.
LDAP_AUTH_OBJECT_CLASS = "inetOrgPerson"

# User model fields mapped to the LDAP
# attributes that represent them.
LDAP_AUTH_USER_FIELDS = {
    "username": "cn",
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

# A tuple of django model fields used to uniquely identify a user.
LDAP_AUTH_USER_LOOKUP_FIELDS = ("username",)

# Path to a callable that takes a dict of {model_field_name: value},
# returning a dict of clean model data.
# Use this to customize how data loaded from LDAP is saved to the User model.
LDAP_AUTH_CLEAN_USER_DATA = "django_python3_ldap.utils.clean_user_data"

# Path to a callable that takes a user model and a dict of {ldap_field_name: [value]},
# and saves any additional user relationships based on the LDAP data.
# Use this to customize how data loaded from LDAP is saved to User model relations.
# For customizing non-related User model fields, use LDAP_AUTH_CLEAN_USER_DATA.
# LDAP_AUTH_SYNC_USER_RELATIONS = "django_python3_ldap.utils.sync_user_relations"
LDAP_AUTH_SYNC_USER_RELATIONS = "nwscandb.ldap_auth.custom_sync_user_relations"

LDAP_AUTH_SYNC_USER_RELATIONS_GROUPS = {
    "staff": "cn=django_nwscandb_staff,ou=groups,dc=denm,dc=de",
    "superuser": "cn=django_nwscandb_superuser,ou=groups,dc=denm,dc=de"
}

# Path to a callable that takes a dict of {ldap_field_name: value},
# returning a list of [ldap_search_filter]. The search filters will then be AND'd
# together when creating the final search filter.
#LDAP_AUTH_FORMAT_SEARCH_FILTERS = "django_python3_ldap.utils.format_search_filters"
LDAP_AUTH_FORMAT_SEARCH_FILTERS = "nwscandb.ldap_auth.custom_format_search_filters"


# my custom search filter checks for "memberOf" (objectclass: groupOfNames) having this group:
#
LDAP_AUTH_MEMBER_OF_ATTRIBUTE = "memberOf"
LDAP_AUTH_GROUP_MEMBER_OF = "cn=django_nwscandb,ou=groups,dc=denm,dc=de"


# Path to a callable that takes a dict of {model_field_name: value}, and returns
# a string of the username to bind to the LDAP server.
# Use this to support different types of LDAP server.
LDAP_AUTH_FORMAT_USERNAME = "django_python3_ldap.utils.format_username_openldap"

# Sets the login domain for Active Directory users.
LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN = None

# The LDAP username and password of a user for authenticating the `ldap_sync_users`
# management command. Set to None if you allow anonymous queries.
LDAP_AUTH_CONNECTION_USERNAME = None  # set in settings_prod_secret.py
LDAP_AUTH_CONNECTION_PASSWORD = None  # set in settings_prod_secret.py


ROOT_URLCONF = 'nwscandb.urls'

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

"""
TEMPLATE_LOADERS = (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
            'django.template.loaders.eggs.Loader',
)
"""

WSGI_APPLICATION = None  # defined for dev/prod separately


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = None  # defined individually (dev/prod)

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/nwscandb.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'nwscandb': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
        'dbimport': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
        'multidns': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
        'nmap': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
        'accounts': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

# User dir: app_name + /static/ + app_name for app specific!
STATIC_URL = "/static/"

""" http://blog.doismellburning.co.uk/django-and-static-files/
Update: To be absolutely clear, STATIC_ROOT should live outside of your Django
project – it's the directory to where your static files are collected, for use
by a local webserver or similar; Django's involvement with that directory should
end once your static files have been collected there
"""

# used for bash$ manage.py collectstatic (useful for collecting for production web server)
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# this is used for common/shared assets (e.g. jquery is used in multiple apps)
# http://vincesalvino.blogspot.de/2013/02/share-static-files-between-apps-in.html
STATICFILES_DIRS = [os.path.join(BASE_DIR, "common-static"), ]


CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'

CRISPY_TEMPLATE_PACK = 'bootstrap3'


