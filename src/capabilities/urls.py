from django.conf.urls import url

from .views import capabilities

urlpatterns = (url(r'^$', capabilities, name='capabilities'), )
