from django.conf import settings
from rest_framework.renderers import BrowsableAPIRenderer


class BrowsableAPIRendererWithCustomAuth(BrowsableAPIRenderer):
    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context["AUTHENTICATION"] = settings.AUTHENTICATION
        return context
