from django.apps import AppConfig


class InitializationConfig(AppConfig):
    """
    The first application to load. This application is responsible
    for initializing the hardware components and loading actions.
    This ensures the components are initialized in the appropriate
    order and available for the other applications.
    """

    name = "initialization"
