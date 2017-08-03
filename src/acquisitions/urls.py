from django.conf.urls import url

from .views import (AcquisitionsOverviewViewSet, AcquisitionViewSet)


urlpatterns = (
    url(r'^$',
        view=AcquisitionsOverviewViewSet.as_view({
            'get': 'list'
        }),
        name='acquisitions-overview'),
    url(r'^(?P<schedule_entry_name>[\w-]+)/$',
        view=AcquisitionViewSet.as_view({
            'get': 'list',
            'delete': 'destroy_all'
        }),
        name='acquisition-list',
        initkwargs={'suffix': 'List'}),
    url(r'^(?P<schedule_entry_name>[\w-]+)/(?P<task_id>\d+)/$',
        view=AcquisitionViewSet.as_view({
            'get': 'retrieve',
            'delete': 'destroy'
        }),
        name='acquisition-detail',
        initkwargs={'suffix': 'Detail'}),
    url(r'^(?P<schedule_entry_name>[\w-]+)/(?P<task_id>\d+)/archive$',
        view=AcquisitionViewSet.as_view({
            'get': 'archive',
        }),
        name='acquisition-archive')
)
