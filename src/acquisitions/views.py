from django.shortcuts import get_object_or_404
from rest_framework.decorators import detail_route
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ViewSet

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

    # def list(self, request):
    #     queryset = self.get_queryset()
    #     context = {'request': request}
    #     serializer_class = self.get_serializer_class()
    #     serializer = serializer_class(queryset, many=True, context=context)
    #     return Response(serializer.data)


class AcquisitionsPreviewViewSet(GenericViewSet):
    lookup_field = 'schedule_entry_name'
    serializer_class = AcquisitionPreviewSerializer
    queryset = ScheduleEntry.objects.select_related()

    def get_object(self):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)  # Apply any filter backends
        filter = {'name': self.kwargs['schedule_entry_name']}
        return get_object_or_404(queryset, **filter)

    def retrieve(self, request, schedule_entry_name):
        entry = self.get_object()
        context = {'request': request}
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(entry.acquisitions.all(),
                                      many=True,
                                      context=context)
        return Response(serializer.data)

    def destroy(self, request, schedule_entry_name):
        entry = self.get_object()
        entry.acquisitions.delete()
        # TODO: what reponse to return?


class AcquisitionMetadataViewSet(MultipleFieldLookupMixin,
                                 mixins.RetrieveModelMixin,
                                 mixins.DestroyModelMixin,
                                 GenericViewSet):
    queryset = Acquisition.objects.all()
    serializer_class = AcquisitionMetadataSerializer
    lookup_fields = ('schedule_entry__name', 'task_id')

    @detail_route
    def sigmf(self, request, schedule_entry__name, task_id):
        pass
