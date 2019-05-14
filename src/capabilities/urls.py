from django.urls import path

from .views import capabilities_view

urlpatterns = (
    path('', capabilities_view, name='capabilities'),
)
