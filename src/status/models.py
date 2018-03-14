from django.db import models


class Location(models.Model):
    """Holds the current longitude and latitude of the sensor.

    Primarily used for mapping and geo-filtering.

    """
    longitude = models.DecimalField(
        max_digits=8,
        decimal_places=5,
        help_text="Longitude of the sensor in decimal degrees.",
    )
    latitude = models.DecimalField(
        max_digits=8,
        decimal_places=5,
        help_text="Longitude of the sensor in decimal degrees.",
    )
