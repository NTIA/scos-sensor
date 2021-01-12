from django.conf import settings
from rest_framework.renderers import BrowsableAPIRenderer


class BrowsableAPIRendererWithCustomAuth(BrowsableAPIRenderer):
    def get_context(self, *args, **kwargs):
        """
        Adds authentication method to browsable API context,
        adapted from https://bradmontgomery.net/blog/disabling-forms-django-rest-frameworks-browsable-api/
        """
        context = super().get_context(*args, **kwargs)
        context["AUTHENTICATION"] = settings.AUTHENTICATION
        return context
