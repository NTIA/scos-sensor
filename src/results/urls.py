from django.urls import path

from .views import (
    ResultsOverviewViewSet, ResultListViewSet, ResultInstanceViewSet)


urlpatterns = (
    path('',
         view=ResultsOverviewViewSet.as_view({
             'get': 'list'
         }),
         name='results-overview'),
    path('<slug:schedule_entry_name>/',
         view=ResultListViewSet.as_view({
             'get': 'list',
             'delete': 'destroy_all'
         }),
         name='result-list'),
    path('<slug:schedule_entry_name>/archive/',
         view=ResultListViewSet.as_view({
             'get': 'archive',
         }),
         name='result-list-archive'),
    path('<slug:schedule_entry_name>/<int:task_id>/',
         view=ResultInstanceViewSet.as_view({
             'get': 'retrieve',
             'delete': 'destroy'
         }),
         name='result-detail'),
    path('<slug:schedule_entry_name>/<int:task_id>/archive',
         view=ResultInstanceViewSet.as_view({
             'get': 'archive',
         }),
         name='result-archive')
)
