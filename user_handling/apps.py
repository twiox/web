from django.apps import AppConfig


class UserHandlingConfig(AppConfig):
    name = 'user_handling'
    
    def ready(self):
        import user_handling.signals
