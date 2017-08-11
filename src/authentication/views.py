from __future__ import absolute_import

from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import User
from .serializers import UserSerializer


class UserViewSet(ModelViewSet):
    """API endpoint that allows users to be viewed or edited."""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return self.queryset

        return self.queryset.filter(pk=user.pk)


class UserAPIView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(pk=user.pk)
