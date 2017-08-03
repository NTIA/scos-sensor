from functools import partial

from django.shortcuts import get_object_or_404
from rest_framework.decorators import detail_route
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from schedule.models import ScheduleEntry
from .models import Acquisition
from .serializers import (AcquisitionsOverviewSerializer,
                          AcquisitionPreviewSerializer,
                          AcquisitionMetadataSerializer)


class MultipleFieldLookupMixin(object):
    """Get multiple field filtering based on a `lookup_fields` attribute."""
    def get_object(self):
        queryset = self.get_queryset()             # Get the base queryset
        queryset = self.filter_queryset(queryset)  # Apply any filter backends
        filter = {
            'schedule_entry__name': self.kwargs['schedule_entry_name'],
            'task_id': self.kwargs['task_id']
        }
        return get_object_or_404(queryset, **filter)  # Lookup the object


class AcquisitionsOverviewViewSet(mixins.ListModelMixin, GenericViewSet):
    lookup_field = 'schedule_entry_name'
    queryset = ScheduleEntry.objects.all()
    serializer_class = AcquisitionsOverviewSerializer


class AcquisitionsPreviewViewSet(mixins.RetrieveModelMixin,
                                 mixins.DestroyModelMixin,
                                 GenericViewSet):
    lookup_field = 'schedule_entry_name'
    serializer_class = partial(AcquisitionPreviewSerializer, many=True)
    queryset = ScheduleEntry.objects.select_related()

    def get_object(self):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)  # Apply any filter backends
        filter = {'name': self.kwargs['schedule_entry_name']}
        entry = get_object_or_404(queryset, **filter)
        return entry.acquisitions.all()


class AcquisitionMetadataViewSet(MultipleFieldLookupMixin,
                                 mixins.RetrieveModelMixin,
                                 mixins.DestroyModelMixin,
                                 GenericViewSet):
    queryset = Acquisition.objects.all()
    serializer_class = AcquisitionMetadataSerializer
    lookup_fields = ('schedule_entry__name', 'task_id')

    @detail_route
    def archive(self, request, schedule_entry__name, task_id):
        pass
