from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet

from .models import ScheduleEntry, Request
from .permissions import IsAdminOrOwnerOrReadOnly
from .serializers import (
    CreateScheduleEntrySerializer,
    AdminCreateScheduleEntrySerializer,
    UpdateScheduleEntrySerializer
)


class ScheduleEntryViewSet(ModelViewSet):
    """View and modify the schedule.

    list:
    Retrieves the current schedule.

    create:
    Creates a new schedule entry.

    retrieve:
    Returns the specified schedule entry.

    update:
    Updates the specified schedule entry.

    partial_update:
    Partially updates the specified schedule entry.

    delete:
    Deletes the specified schedule entry.

    """
    queryset = ScheduleEntry.objects.all()
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [
        IsAdminOrOwnerOrReadOnly,
    ]

    def perform_create(self, serializer):
        # import pdb; pdb.set_trace()
        r = Request()
        r.from_drf_request(self.request)
        serializer.save(request=r, owner=self.request.user)

    def get_queryset(self):
        # .list() does not call .get_object(), which triggers permissions
        # checks, so we need to filter our queryset based on `is_private` and
        # request user.
        base_queryset = self.filter_queryset(self.queryset)
        if self.request.user.is_staff:
            return base_queryset
        else:
            return base_queryset.filter(is_private=False)

    def get_serializer_class(self):
        if self.action == 'create':
            if self.request and self.request.user.is_staff:
                return AdminCreateScheduleEntrySerializer
            else:
                return CreateScheduleEntrySerializer
        else:
            return UpdateScheduleEntrySerializer
