from django.conf.urls import url

from .views import (AcquisitionsOverviewViewSet,
                    AcquisitionsPreviewViewSet,
                    AcquisitionMetadataViewSet)


urlpatterns = (
    url(r'^$',
        view=AcquisitionsOverviewViewSet.as_view({
            'get': 'list'
        }),
        name='acquisitions-overview'),
    url(r'^(?P<schedule_entry_name>[\w-]+)/$',
        view=AcquisitionsPreviewViewSet.as_view({
            'get': 'retrieve',
            'delete': 'destroy'
        }),
        name='acquisitions-preview'),
    url(r'^(?P<schedule_entry_name>[\w-]+)/(?P<task_id>\d+)/$',
        view=AcquisitionMetadataViewSet.as_view({
            'get': 'retrieve',
            'delete': 'destroy'
        }),
        name='acquisition-metadata'),
    url(r'^(?P<schedule_entry_name>[\w-]+)/(?P<task_id>\d+)/sigmf$',
        view=AcquisitionMetadataViewSet.as_view({
            'get': 'sigmf',
        }),
        name='acquisition-data')
)
