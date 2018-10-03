from django import template

from sensor.settings import VERSION_STRING

register = template.Library()


@register.simple_tag
def sensor_version_string():
    return VERSION_STRING
