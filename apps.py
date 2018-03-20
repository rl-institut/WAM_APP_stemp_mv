from django.apps import AppConfig
from kopy import settings


class StempConfig(AppConfig):
    name = 'stemp'

    def ready(self):
        # Do this right after settings are set:
        from kopy.sessions import SessionData
        settings.SESSION_DATA = SessionData()
