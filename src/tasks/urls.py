from django.urls import path

from .views import (
    TaskResultsOverviewViewSet, TaskResultListViewSet,
    TaskResultInstanceViewSet, task_root, upcoming_tasks)


urlpatterns = (
    path('', view=task_root, name='task-root'),
    path('upcoming/', view=upcoming_tasks, name='upcoming-tasks'),
    path('completed/',
         view=TaskResultsOverviewViewSet.as_view({
             'get': 'list'
         }),
         name='task-results-overview'),
    path('completed/<slug:schedule_entry_name>/',
         view=TaskResultListViewSet.as_view({
             'get': 'list',
             'delete': 'destroy_all'
         }),
         name='task-result-list'),
    path('completed/<slug:schedule_entry_name>/archive/',
         view=TaskResultListViewSet.as_view({
             'get': 'archive',
         }),
         name='task-result-list-archive'),
    path('completed/<slug:schedule_entry_name>/<int:task_id>/',
         view=TaskResultInstanceViewSet.as_view({
             'get': 'retrieve',
             'delete': 'destroy'
         }),
         name='task-result-detail'),
    path('completed/<slug:schedule_entry_name>/<int:task_id>/archive',
         view=TaskResultInstanceViewSet.as_view({
             'get': 'archive',
         }),
         name='task-result-archive')
)
