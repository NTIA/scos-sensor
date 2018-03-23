from django import template

from sensor.settings import VERSION_STRING


register = template.Library()


@register.simple_tag
def sensor_version_string():
    print("VERSION_STRING: {}".format(VERSION_STRING))
    return VERSION_STRING
