from rest_framework.viewsets import ModelViewSet

from .models import ScheduleEntry
from .serializers import ScheduleEntrySerializer


class ScheduleEntryViewSet(ModelViewSet):
    queryset = ScheduleEntry.objects.filter(canceled=False)
    serializer_class = ScheduleEntrySerializer
    lookup_field = 'name'
