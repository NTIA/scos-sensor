import logging

logger = logging.getLogger(__name__)


class StatusMonitor:
    """
    Singleton the keeps track of all components within the system that can provide
    status.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            logger.debug("Creating the ActionLoader")
            cls._instance = super().__new__(cls)
            cls._instance._status_components = []
        return cls._instance

    @property
    def status_components(self):
        """
        Returns any components that have been registered as status providing.
        """
        return self._status_components

    def add_component(self, component):
        """
        Allows objects to be registered to provide status. Any object registered will
        be included in scos-sensors status endpoint. All objects registered must
        implement a get_status() method that returns a dictionary.

        :param component: the object to add to the list of status providing objects.
        """
        if hasattr(component, "get_status"):
            self._status_components.append(component)
        else:
            logger.debug(
                "Provided component has no `get_status` method and was not registered"
                + f" with the status monitor: {component}"
            )
