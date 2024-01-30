from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def sensor_version_string():
    return settings.VERSION_STRING
