class StatusMonitor:

    def __init__(self):
        self.status_components = []

    def add_component(self, component):
        self.status_components.append(component)
