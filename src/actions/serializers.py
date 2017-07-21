from django.utils.text import re_camel_case

from sensor import settings

from .logger import LoggerSerializer  # noqa


registered_serializers = [
    LoggerSerializer,
]


if settings.DEBUG:
    # import testing/debugging serializers and add to registered_serializers
    pass


by_name = {}


def camel_case_to_snake_case(value: str):
    return re_camel_case.sub(r'_\1', value).strip().lower()


def strip_serializer(value: str):
    return value.split('Serializer')[0]


for serializer in registered_serializers:
    import pdb; pdb.set_trace()
    internal_name = serializer.__class__.__name__
    external_name = camel_case_to_snake_case(strip_serializer(internal_name))
    by_name[external_name] = serializer
