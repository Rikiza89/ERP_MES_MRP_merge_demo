"""
Core App Configuration
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core System'
    
    def ready(self):
        # Import signals when app is ready
        import core.signals
        # Register model signals
        core.signals.register_model_signals()