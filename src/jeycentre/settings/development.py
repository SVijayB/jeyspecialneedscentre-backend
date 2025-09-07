"""
Development settings for jeycentre project.
"""

from .base import *

# Debug settings
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0').split(',')

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Security settings for development
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)


# Logging for development
LOGGING['root']['level'] = config('LOG_LEVEL', default='DEBUG')
LOGGING['root']['handlers'] = ['console']

# Create logs directory if it doesn't exist
import os
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
