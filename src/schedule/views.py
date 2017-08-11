from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import ScheduleEntry
from .permissions import IsAdminOrOwnerOrReadOnly
from .serializers import (CreateScheduleEntrySerializer,
                          UpdateScheduleEntrySerializer)


class ScheduleEntryViewSet(ModelViewSet):
    queryset = ScheduleEntry.objects.all()
    lookup_field = 'name'
    permission_classes = (IsAuthenticated, IsAdminOrOwnerOrReadOnly)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateScheduleEntrySerializer
        else:
            return UpdateScheduleEntrySerializer
