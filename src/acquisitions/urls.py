from django.urls import path

from .views import (AcquisitionsOverviewViewSet, AcquisitionListViewSet,
                    AcquisitionInstanceViewSet)

urlpatterns = (
    path('',
         view=AcquisitionsOverviewViewSet.as_view({
             'get': 'list'
         }),
         name='acquisitions-overview'),
    path('<slug:schedule_entry_name>/',
         view=AcquisitionListViewSet.as_view({
             'get': 'list',
             'delete': 'destroy_all'
         }),
         name='acquisition-list'),
    path('<slug:schedule_entry_name>/archive/',
         view=AcquisitionListViewSet.as_view({
             'get': 'archive',
         }),
         name='acquisition-list-archive'),
    path('<slug:schedule_entry_name>/<int:task_id>/',
         view=AcquisitionInstanceViewSet.as_view({
             'get': 'retrieve',
             'delete': 'destroy'
         }),
         name='acquisition-detail'),
    path('<slug:schedule_entry_name>/<int:task_id>/archive',
         view=AcquisitionInstanceViewSet.as_view({
             'get': 'archive',
         }),
         name='acquisition-archive')
)
