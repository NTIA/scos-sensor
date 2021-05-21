from capabilities import capabilities
from handlers.django_handlers import NotifyLocationAdded, NotifyLocationDeleted
from status.models import GPS_LOCATION_DESCRIPTION, Location


def location_action_completed_callback(sender, **kwargs):
    """Update database and capabilities when GPS is synced or database is updated"""

    if sender is NotifyLocationDeleted or sender is NotifyLocationAdded:
        try:
            update_capabilities()
        except Location.DoesNotExist:
            if "location" in capabilities["sensor"]:
                del capabilities["sensor"]["location"]
    else:
        latitude = kwargs["latitude"]
        longitude = kwargs["longitude"]
        try:
            if latitude and longitude:
                gps_location = Location.objects.get(gps=True)
                gps_location.latitude = latitude
                gps_location.longitude = longitude
                gps_location.save()
        except Location.DoesNotExist:
            gps_location = Location.objects.create(
                gps=True,
                description=GPS_LOCATION_DESCRIPTION,
                latitude=latitude,
                longitude=longitude,
            )
        update_capabilities()


def update_capabilities():
    active_location = Location.objects.get(active=True)
    capabilities["sensor"]["location"] = {
        "x": active_location.longitude,
        "y": active_location.latitude,
    }
    if active_location.description:
        capabilities["sensor"]["location"]["description"] = active_location.description
