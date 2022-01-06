from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    name = 'scheduler'
    label= 'schedulerLabel'

    def ready(self):
        from . import updater
        updater.start()
