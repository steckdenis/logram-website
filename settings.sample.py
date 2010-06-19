# -*- coding: utf-8 -*-
# Django settings for pyv4 project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

ugettext = lambda s: s

LANGUAGES = (
    ('fr', ugettext('Français')),
    ('en', ugettext('Anglais (beta)')),
)

MANAGERS = ADMINS

# Session
SESSION_ENGINE = 'django.contrib.sessions.backends.file'

DATABASES = {
    'default': {
        'NAME': 'votre base',
        'ENGINE': 'mysql',
        'USER': 'un nom',
        'PASSWORD': 'mot de passe de la BDD'
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Brussels'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'fr-fr'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
#
# Remplacez "là/où/est/logram" par le dossier dans lequel se trouve pyv4/
MEDIA_ROOT = '/là/où/est/logram/pyv4/files'
STYLE_ROOT = '/là/où/est/logram/pyv4/style'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = 'http://localhost:8000/files/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'plein de caractères bizarres, illimité'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.debug',
    'django.core.context_processors.request',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'pyv4.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '/là/où/est/logram/pyv4/templates',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.markup',
    'pyv4.general',
    'pyv4.news',
    'pyv4.upload',
    'pyv4.users',
    'pyv4.forum',
    'pyv4.wiki',
    'pyv4.packages',
    'pyv4.demands',
    'pyv4.mp',
    'pyv4.feeds',
    'pyv4.pastebin',
    'djapian',
)

#Login
LOGIN_URL = 'login.html'
LOGIN_REDIRECT_URL = '/'
DEFAULT_GROUP_NAME = 'Utilisateur'

INTERNAL_IPS = ('127.0.0.1')

AUTH_PROFILE_MODULE = 'general.profile'

# Cache
CACHE_BACKEND = 'file:///tmp/django_cache'

# WebSVN
WEBSVN_BASE = 'svn://logram-project.org/logram'

# Gestion des paquets
LOCAL_MIRROR = '/home/steckdenis/repo/'  # Dossier local qui contient le dépôt de paquets
PACKAGES_PASSWORD = 'un pitit mdp' # Mot de passe que doit fournir le script update_repo à la vue packages.update_database
UPLOAD_PASSWORD = 'un autre mdp' # Mot de passe pour construire les clefs d'upload

# Recherche
DJAPIAN_DATABASE_PATH = './djapiandb/'

# Emails
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBacked' # Remplacez "console" par "smtp" pour réellement envoyer les mails
EMAIL_HOST = 'localhost'
EMAIL_PORT = '' # Port email SMTP
EMAIL_HOST_USER = '' # L'utilisateur SMTP
EMAIL_HOST_PASSWORD = '' # Mdp SMTP
EMAIL_USE_TLS = False # Utiliser ou pas une connexion sécurisée
