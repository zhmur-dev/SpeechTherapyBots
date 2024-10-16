from django.apps import AppConfig

from core.localization import APP_NAME


class CoreConfig(AppConfig):
    name = 'core'
    verbose_name = APP_NAME
