from django.conf.urls import url

from .views import AcquisitionsOverviewViewSet, AcquisitionViewSet


urlpatterns = (
    url(r'^$',
        view=AcquisitionsOverviewViewSet.as_view({
            'get': 'list'
        }),
        name='acquisitions-list'),
    url(r'^(?P<schedule_entry_name>[\w-]+)/$',
        view=AcquisitionsOverviewViewSet.as_view({
            'get': 'retrieve',
            'delete': 'destroy'
        }),
        name='acquisitions-detail'),
    url(r'^(?P<schedule_entry_name>[\w-]+)/(?P<task_id>\d+)/$',
        view=AcquisitionViewSet.as_view({
            'get': 'retrieve',
            'delete': 'destroy'
        }),
        name='acquisition-metadata'),
    url(r'^(?P<schedule_entry_name>[\w-]+)/(?P<task_id>\d+)/sigmf$',
        view=AcquisitionViewSet.as_view({
            'get': 'sigmf',
        }),
        name='acquisition-data')
)
