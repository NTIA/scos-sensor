from django.conf.urls import url

from .views import (ResultsOverviewViewSet, ResultListViewSet,
                    ResultInstanceViewSet)

urlpatterns = (url(
    r'^$',
    view=ResultsOverviewViewSet.as_view({
        'get': 'list'
    }),
    name='results-overview'),
               url(r'^(?P<schedule_entry_name>[\w-]+)/$',
                   view=ResultListViewSet.as_view({
                       'get': 'list',
                   }),
                   name='result-list'),
               url(r'^(?P<schedule_entry_name>[\w-]+)/(?P<task_id>\d+)/$',
                   view=ResultInstanceViewSet.as_view({
                       'get': 'retrieve',
                   }),
                   name='result-detail'))
