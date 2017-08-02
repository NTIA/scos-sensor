from rest_framework.viewsets import ModelViewSet

from .models import ScheduleEntry
from .serializers import ScheduleEntrySerializer


class ScheduleEntryViewSet(ModelViewSet):
    queryset = ScheduleEntry.objects.all()
    serializer_class = ScheduleEntrySerializer
    lookup_field = 'name'
