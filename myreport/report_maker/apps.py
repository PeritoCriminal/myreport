from django.apps import AppConfig


class ReportMakerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "report_maker"

    def ready(self):
        from . import signals  # noqa
