from django.apps import AppConfig
from wam import settings


class StempConfig(AppConfig):
    name = 'stemp'

    def ready(self):
        # Do this right after settings are set:
        from wam.sessions import SessionData
        settings.SESSION_DATA = SessionData()
