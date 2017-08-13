from django.conf.urls import url

from .views import capabilities_view


urlpatterns = (
    url(r'^$', capabilities_view, name='capabilities'),
)
