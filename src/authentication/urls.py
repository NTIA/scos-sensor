from django.urls import path

from .views import UserDetailsListView, UserDetailsView

urlpatterns = (
    path("", UserDetailsListView.as_view(), name="user-list"),
    path("me/", UserDetailsView.as_view(), name="user-detail"),
    path("<int:pk>/", UserDetailsView.as_view(), name="user-detail"),
)
