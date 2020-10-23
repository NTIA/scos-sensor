from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from .models import User
from .serializers import UserDetailsSerializer


class UserDetailsListView(ListCreateAPIView):
    """View user details and create users."""

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserDetailsSerializer


class UserDetailsView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailsSerializer
