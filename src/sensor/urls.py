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
from rest_framework.documentation import include_docs_urls
from rest_framework.renderers import BrowsableAPIRenderer, CoreJSONRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.schemas import get_schema_view
from rest_framework.urlpatterns import format_suffix_patterns

from .schema import OpenAPIRenderer
from .settings import API_TITLE, API_DESCRIPTION


@api_view(('GET',))
def api_v1_root(request, format=None):
    reverse_ = partial(reverse, request=request, format=format)
    list_endpoints = {
        'schedule': reverse_('v1:schedule-list'),
        'acquisitions': reverse_('v1:acquisitions-overview'),
        'status': reverse_('v1:status'),
        'users': reverse_('v1:user-list'),
        'capabilities': reverse_('v1:capabilities')
    }

    return Response(list_endpoints)


api_v1_urlpatterns = format_suffix_patterns((
    url(r'^$', api_v1_root, name='api-root'),
    url(r'^acquisitions/', include('acquisitions.urls')),
    url(r'^capabilities/', include('capabilities.urls')),
    url(r'^schedule/', include('schedule.urls')),
    url(r'^status', include('status.urls')),
    url(r'^users/', include('authentication.urls')),
    url(r'^schema', get_schema_view(
        title=API_TITLE,
        description=API_DESCRIPTION,
        renderer_classes=(
            BrowsableAPIRenderer,
            OpenAPIRenderer,
            CoreJSONRenderer
        )
    )),
))

urlpatterns = (
    # TODO: root should be mkdocs page
    url(r'^$', RedirectView.as_view(url='/api/')),
    url(r'^api/$', RedirectView.as_view(url='/api/v1/')),
    # FIXME: docs not detecting routes
    url(r'^api/docs/', include_docs_urls(title=API_TITLE,
                                         description=API_DESCRIPTION)),
    url(r'^api/v1/', include(api_v1_urlpatterns, namespace='v1')),
    url(r'^api/auth/', include('rest_framework.urls')),
)
