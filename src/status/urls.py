from django.urls import path

from .views import status

urlpatterns = (path("", status, name="status"),)
