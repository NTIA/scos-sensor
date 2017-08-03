from rest_framework.viewsets import ModelViewSet

from .models import ScheduleEntry
from .serializers import (CreateScheduleEntrySerializer,
                          UpdateScheduleEntrySerializer)


class ScheduleEntryViewSet(ModelViewSet):
    queryset = ScheduleEntry.objects.all()
    lookup_field = 'name'

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateScheduleEntrySerializer
        else:
            return UpdateScheduleEntrySerializer
