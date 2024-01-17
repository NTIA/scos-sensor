import logging

logger = logging.getLogger(__name__)

class StatusMonitor(object):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            logger.debug('Creating the ActionLoader')
            cls._instance = super(StatusMonitor, cls).__new__(cls)
            cls._instance.status_components = []
        return cls._instance

    def add_component(self, component):
        """
        Allows objects to be registered to provide status. Any object registered will
        be included in scos-sensors status endpoint. All objects registered must
        implement a get_status() method that returns a dictionary.

        :param component: the object to add to the list of status providing objects.
        """
        if hasattr(component, "get_status"):
            self.status_components.append(component)

