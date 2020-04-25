from django.apps import AppConfig


class MembersConfig(AppConfig):
    name = 'members'
    
    def ready(self):
        import user_handling.signals #important, if we have signals
