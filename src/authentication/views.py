from __future__ import absolute_import

from django.contrib.auth.models import User, Group
from rest_framework.viewsets import ModelViewSet

from .serializers import UserSerializer, GroupSerializer


class UserViewSet(ModelViewSet):
    """API endpoint that allows users to be viewed or edited."""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(ModelViewSet):
    """API endpoint that allows groups to be viewed or edited."""
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
