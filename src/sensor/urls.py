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

from functools import partial

from django.conf.urls import include, url
from django.views.generic import RedirectView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.urlpatterns import format_suffix_patterns


@api_view(('GET',))
def api_v1_root(request, format=None):
    reverse_ = partial(reverse, request=request, format=format)
    return Response({
        'schedule': reverse_('v1:schedule-list'),
        'acquisitions': reverse_('v1:acquisitions-overview'),
        'status': reverse_('v1:status-list'),
        'users': reverse_('user-list'),
    })


api_v1_urlpatterns = format_suffix_patterns((
    url(r'^$', api_v1_root, name='api-root'),
    url(r'^acquisitions/', include('acquisitions.urls')),
    url(r'^schedule/', include('schedule.urls')),
    url(r'^status/', include('status.urls'))
))

urlpatterns = (
    url(r'^$', RedirectView.as_view(url='/api/')),
    url(r'^api/$', RedirectView.as_view(url='/api/v1/')),
    url(r'^api/', include('authentication.urls')),
    url(r'^api/v1/', include(api_v1_urlpatterns, namespace='v1')),
    url(r'^api/auth/', include('rest_framework.urls'))
)
