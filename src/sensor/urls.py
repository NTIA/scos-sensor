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

from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from scheduler.views import ScheduleEntryViewSet, SchedulerViewSet
from acquisitions.views import AcquisitionViewSet


api_v1_router = DefaultRouter()
api_v1_router.register(r'schedule', ScheduleEntryViewSet, base_name='schedule')
api_v1_router.register(r'scheduler', SchedulerViewSet, base_name='scheduler')
api_v1_router.register(r'acquisitions', AcquisitionViewSet, base_name='acquisitions')

urlpatterns = [
    url(r'^api/v1/', include(api_v1_router.urls, namespace='api_v1')),
    url(r'^api/auth/', include('rest_framework.urls',
                               namespace='rest_framework'))
]
