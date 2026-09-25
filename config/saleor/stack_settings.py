"""Django settings of the Docker stack: Saleor's settings plus the `stack` app.

Selected with DJANGO_SETTINGS_MODULE=stack_settings (PYTHONPATH=/opt/stack).
Everything else is configured with Saleor's own environment variables.
"""

from saleor.settings import *  # noqa: F403

INSTALLED_APPS = [*INSTALLED_APPS, "stack"]  # noqa: F405
