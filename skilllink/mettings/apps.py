from django.apps import AppConfig


class MettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mettings'

    def ready(self):
        import mettings.signals
