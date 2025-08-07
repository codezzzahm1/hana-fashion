from django.apps import AppConfig


class ShoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sho'

    def ready(self):
        import sho.signals 