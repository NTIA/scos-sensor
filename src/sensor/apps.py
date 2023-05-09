from django.apps import AppConfig


class SensorConfig(AppConfig):
    name = "sensor"

    def ready(self) -> None:
        import sensor.schema

        return
