from django.conf.urls import url

from .views import status_view


urlpatterns = (
    url(r'^$', status_view, name='status'),
)
