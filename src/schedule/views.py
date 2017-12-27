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
    """GET /api/v1/schedule/

    create:
    Create a new schedule.

    partial_update:
    Partially updates a specified Schedule Entry.

    update:
    Updates a specified Schedule Entry.

    delete:
    Deletes a specified Schedule Entry.

    retrieve:
    Returns a specified Schedule Entry.
    """
    queryset = ScheduleEntry.objects.all()
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [
        IsAdminOrOwnerOrReadOnly,
    ]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_serializer_class(self):
        """Get"""
        if self.action == 'create':
            if self.request and self.request.user.is_staff:
                return AdminCreateScheduleEntrySerializer
            else:
                return CreateScheduleEntrySerializer
        else:
            return UpdateScheduleEntrySerializer
