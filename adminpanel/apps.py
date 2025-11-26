from django.apps import AppConfig


class AdminpanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'adminpanel'
    verbose_name = 'Admin Panel'
    
    def ready(self):
        # import signals to ensure post_save handlers are connected
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
