from django.conf.urls import url

from .views import (AcquisitionsOverviewViewSet,
                    AcquisitionListViewSet,
                    AcquisitionInstanceViewSet)


urlpatterns = (
    url(r'^$',
        view=AcquisitionsOverviewViewSet.as_view({
            'get': 'list'
        }),
        name='acquisitions-overview'),
    url(r'^(?P<schedule_entry_name>[\w-]+)/$',
        view=AcquisitionListViewSet.as_view({
            'get': 'list',
            'delete': 'destroy_all'
        }),
        name='acquisition-list'),
    url(r'^(?P<schedule_entry_name>[\w-]+)/(?P<task_id>\d+)/$',
        view=AcquisitionInstanceViewSet.as_view({
            'get': 'retrieve',
            'delete': 'destroy'
        }),
        name='acquisition-detail'),
    url(r'^(?P<schedule_entry_name>[\w-]+)/(?P<task_id>\d+)/archive$',
        view=AcquisitionInstanceViewSet.as_view({
            'get': 'archive',
        }),
        name='acquisition-archive')
)
