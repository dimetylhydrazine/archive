from .base import *

DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Static через django.contrib.staticfiles
# Media через static() в urls.py — работает в dev