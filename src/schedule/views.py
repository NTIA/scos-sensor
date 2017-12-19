from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet

from .models import ScheduleEntry
from .permissions import IsAdminOrOwnerOrReadOnly
from .serializers import (
    CreateScheduleEntrySerializer,
    AdminCreateScheduleEntrySerializer,
    UpdateScheduleEntrySerializer
)


class ScheduleEntryViewSet(ModelViewSet):
    queryset = ScheduleEntry.objects.all()
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [
        IsAdminOrOwnerOrReadOnly,
    ]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            if self.request and self.request.user.is_staff:
                return AdminCreateScheduleEntrySerializer
            else:
                return CreateScheduleEntrySerializer
        else:
            return UpdateScheduleEntrySerializer
