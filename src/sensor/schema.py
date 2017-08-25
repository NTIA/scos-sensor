# This file patches OpenAPIRenderer and OpenAPICodec from django-rest-swagger
# in order to respect requested JSON indentation.
# PR is pending here:
# https://github.com/marcgibbons/django-rest-swagger/pull/697

import coreapi
from coreapi.compat import force_bytes
from openapi_codec import OpenAPICodec as _OpenAPICodec
from openapi_codec.encode import generate_swagger_object
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework import status
import simplejson as json

from .settings import SWAGGER_SETTINGS


class OpenAPICodec(_OpenAPICodec):
    def encode(self, document, extra=None, **options):
        if not isinstance(document, coreapi.Document):
            raise TypeError('Expected a `coreapi.Document` instance')

        data = generate_swagger_object(document)
        if isinstance(extra, dict):
            data.update(extra)

        indent = options.get('indent')
        return force_bytes(json.dumps(data, indent=indent))


class OpenAPIRenderer(BaseRenderer):
    media_type = 'application/openapi+json'
    charset = None
    format = 'openapi'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context['response'].status_code != status.HTTP_200_OK:
            return JSONRenderer().render(data)
        extra = self.get_customizations()

        indent = None
        if isinstance(renderer_context, dict):
            indent = renderer_context.get('indent')

        return OpenAPICodec().encode(data, extra=extra, indent=indent)

    def get_customizations(self):
        """
        Adds settings, overrides, etc. to the specification.
        """
        data = {}
        securitydefs = SWAGGER_SETTINGS.get('SECURITY_DEFINITIONS')
        if securitydefs:
            data['securityDefinitions'] = securitydefs

        return data
