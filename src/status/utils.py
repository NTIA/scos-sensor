import logging

from .models import Location

logger = logging.getLogger(__name__)


def get_location():
    """Returns Location object JSON if set or None and logs an error."""
    try:
        return Location.objects.filter(active=True).get()
    except Location.DoesNotExist:
        logger.error("You must create a Location in /admin.")
        return None
