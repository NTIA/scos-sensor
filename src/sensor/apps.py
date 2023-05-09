from django.apps import AppConfig


class SensorConfig(AppConfig):
    name = "sensor"

    def ready(self) -> None:
        import authentication.schema

        return
