"""
Settings package for jeycentre project.
Loads the appropriate settings module based on DJANGO_SETTINGS_MODULE.
"""

import os
from decouple import config

# Determine which settings to use
ENVIRONMENT = config('DJANGO_ENVIRONMENT', default='development')

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'development':
    from .development import *
else:
    from .development import *  # Default to development
