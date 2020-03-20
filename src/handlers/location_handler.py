from status.models import GPS_LOCATION_DESCRIPTION, Location


def location_action_completed_callback(sender, **kwargs):
    latitude = kwargs["latitude"]
    longitude = kwargs["longitude"]

    try:
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

