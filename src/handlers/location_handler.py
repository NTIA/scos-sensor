from status.models import GPS_LOCATION_DESCRIPTION, Location
from scos_actions.capabilities import capabilities

def location_action_completed_callback(sender, **kwargs):
    """Update database and capabilities when GPS is synced or database is updated"""

    latitude = kwargs["latitude"] if "latitude" in kwargs else None
    longitude = kwargs["longitude"] if "longitude" in kwargs else None
    gps = kwargs["gps"] if "gps" in kwargs else None
    description = kwargs["description"] if "description" in kwargs else None
    height = kwargs["height"] if "height" in kwargs else None

    try:
        location = Location.objects.get(active=True)
    except Location.DoesNotExist:
        location = Location()
    if latitude and longitude:
        location.latitude = latitude
        location.longitude = longitude
    if gps:
        location.gps = True
    if description:
        location.description = description
    if height:
        location.height = height
    location.active = True
    location.save()


def db_location_updated(sender, **kwargs):
    instance = kwargs["instance"]
    if isinstance(instance, Location):
        if 'location' not in capabilities['sensor']:
            capabilities['sensor']['location'] = {}
        capabilities['sensor']['location']['x'] = instance.longitude
        capabilities['sensor']['location']['y'] = instance.latitude
        capabilities['sensor']['location']['z'] = instance.height
        capabilities['sensor']['location']['description'] = instance.description
