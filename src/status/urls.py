from django.urls import path

from .views import status_view

urlpatterns = (path("", status_view, name="status"),)
