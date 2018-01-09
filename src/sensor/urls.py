"""scos_sensor URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/

Examples:

Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))

"""

from __future__ import absolute_import

from functools import partial

from django.conf.urls import include, url
from django.views.generic import RedirectView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.urlpatterns import format_suffix_patterns

from .settings import REST_FRAMEWORK
from .views import SchemaView


# Matches api/v1, api/v2, etc...
API_PREFIX = r'^api/(?P<version>v[0-9]+)/'
DEFAULT_API_VERSION = REST_FRAMEWORK['DEFAULT_VERSION']


@api_view(('GET',))
def api_v1_root(request, version, format=None):
    """SCOS sensor API root."""
    reverse_ = partial(reverse, request=request, format=format)
    list_endpoints = {
        'schedule': reverse_('schedule-list'),
        'acquisitions': reverse_('acquisitions-overview'),
        'status': reverse_('status'),
        'users': reverse_('user-list'),
        'capabilities': reverse_('capabilities')
    }

    return Response(list_endpoints)


api_urlpatterns = format_suffix_patterns((
    url(r'^$', api_v1_root, name='api-root'),
    url(r'^acquisitions/', include('acquisitions.urls')),
    url(r'^capabilities/', include('capabilities.urls')),
    url(r'^schedule/', include('schedule.urls')),
    url(r'^status', include('status.urls')),
    url(r'^users/', include('authentication.urls')),
    url(r'^schema/$', SchemaView.as_view(), name='api_schema')
))

urlpatterns = (
    url(r'^$', RedirectView.as_view(url='/api/')),
    url(r'^api/$',
        RedirectView.as_view(url='/api/{}/'.format(DEFAULT_API_VERSION))),
    url(API_PREFIX, include(api_urlpatterns)),
    url(API_PREFIX, include('drf_openapi.urls')),
    url(r'^api/auth/', include('rest_framework.urls')),
)
