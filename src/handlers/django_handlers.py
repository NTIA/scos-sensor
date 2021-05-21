from scos_actions.actions.interfaces.signals import location_action_completed

from status.models import Location


class NotifyLocationDeleted:
    """Notify location_action_completed that Location was deleted."""


class NotifyLocationAdded:
    """Notify location_action_completed that Location was added."""


def post_delete_callback(sender, **kwargs):
    if sender is Location:
        location_action_completed.send(
            NotifyLocationDeleted, latitude=None, longitude=None
        )


def post_save_callback(sender, **kwargs):
    if sender is Location:
        location_action_completed.send(
            NotifyLocationAdded, latitude=None, longitude=None
        )
