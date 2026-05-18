from django.apps import AppConfig


class HelloappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'helloapp'
    verbose_name = 'AutoBoard'

    def ready(self):
        import helloapp.signals  # noqa: F401
