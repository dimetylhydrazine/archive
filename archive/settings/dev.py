from .base import *

DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Static через django.contrib.staticfiles
# Media через static() в urls.py — работает в dev

INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
INTERNAL_IPS = ['127.0.0.1']