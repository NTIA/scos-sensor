from status import status_monitor


def register_component_with_status_completed_callback(sender, **kwargs):
    status_monitor.add_component(kwargs['component'])
