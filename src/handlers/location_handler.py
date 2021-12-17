from status.models import GPS_LOCATION_DESCRIPTION, Location


def location_action_completed_callback(sender, **kwargs):
    """Update database and capabilities when GPS is synced or database is updated"""
    latitude = kwargs["latitude"]
    longitude = kwargs["longitude"]
    try:
        if latitude and longitude:
            gps_location = Location.objects.get(gps=True)
            gps_location.latitude = latitude
            gps_location.longitude = longitude
            gps_location.active = True
            gps_location.save()
    except Location.DoesNotExist:
        # if there is an active location, use its description
        # in new GPS location
        if Location.objects.filter(active=True).exists():
            active_location = Location.objects.get(active=True)
            description = active_location.description
        else:
            description = ""
        gps_location = Location.objects.create(
            gps=True,
            latitude=latitude,
            longitude=longitude,
            description=description
        )
