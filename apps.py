
from django.apps import AppConfig

from wam import settings
from stemp import app_settings


class StempConfig(AppConfig):
    name = 'stemp'

    def ready(self):
        """This function is executed right after project settings"""

        # Initialize stemp sessions:
        from wam.sessions import SessionData
        settings.SESSION_DATA = SessionData()
