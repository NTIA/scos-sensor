from django.conf.urls import url

from .views import UserListView, UserInstanceView


urlpatterns = (
    url(r'^$', UserListView.as_view(), name='user-list'),
    url(r'^me/$', UserInstanceView.as_view(), name='user-detail'),
    url(r'^(?P<pk>\d+)$', UserInstanceView.as_view(), name='user-detail'),
)
