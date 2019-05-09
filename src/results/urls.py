from django.urls import path

from .views import (ResultsOverviewViewSet, ResultListViewSet,
                    ResultInstanceViewSet)

urlpatterns = (
    path('',
         view=ResultsOverviewViewSet.as_view({'get': 'list'}),
         name='results-overview'),
    path('<slug:schedule_entry_name>/',
         view=ResultListViewSet.as_view({
             'get': 'list',
         }),
         name='result-list'),
    path('<slug:schedule_entry_name>/<int:task_id>/',
         view=ResultInstanceViewSet.as_view({
             'get': 'retrieve',
         }),
         name='result-detail')
)
