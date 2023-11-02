"""Request model to save enough of a request to be passed to reverse()."""

from django.db import models
from django.utils.encoding import iri_to_uri
from django.utils.functional import cached_property
from rest_framework.versioning import URLPathVersioning


class Request(models.Model):
    """Save enough of a request to be passed to reverse()."""

    scheme = models.CharField(max_length=16, blank=True, null=True)
    version = models.CharField(max_length=16, blank=True, null=True)
    host = models.CharField(max_length=255, blank=True, null=True)

    def build_absolute_uri(self, location=None):
        """Called from within Django reverse."""
        scheme_host = f"{self.scheme}://{self.host}"
        return iri_to_uri(scheme_host + location)

    def from_drf_request(self, request, commit=True):
        self.host = request._request.get_host()
        self.scheme = request._request.scheme
        self.version = request.version

        if commit:
            self.save()

    @cached_property
    def GET(self):
        """Query parameters"""
        return {}

    @cached_property
    def versioning_scheme(self):
        return URLPathVersioning()
