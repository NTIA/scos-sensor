from django.shortcuts import get_object_or_404
from rest_framework.decorators import detail_route
from rest_framework.generics import RetrieveDestroyAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from schedule.models import ScheduleEntry
from .models import Acquisition
from .serializers import AcquisitionSerializer, AcquisitionsOverviewSerializer


class MultipleFieldLookupMixin(object):
    """Get multiple field filtering based on a `lookup_fields` attribute."""
    def get_object(self):
        queryset = self.get_queryset()             # Get the base queryset
        queryset = self.filter_queryset(queryset)  # Apply any filter backends
        filter = {}
        for field in self.lookup_fields:
            if self.kwargs[field]:  # Ignore empty fields.
                filter[field] = self.kwargs[field]
        return get_object_or_404(queryset, **filter)  # Lookup the object


class AcquisitionsOverviewViewSet(ViewSet):
    lookup_field = 'schedule_entry_name'

    def list(self, request):
        queryset = ScheduleEntry.objects.all()
        context = {'request': request}
        serializer = AcquisitionsOverviewSerializer(queryset,
                                                    many=True,
                                                    context=context)
        return Response(serializer.data)

    def retrieve(self, request, schedule_entry_name):
        queryset = ScheduleEntry.objects\
                                .select_related()\
                                .filter(name=schedule_entry_name)
        entry = get_object_or_404(queryset, name=schedule_entry_name)
        context = {'request': request}
        serializer = AcquisitionSerializer(entry.acquisitions,
                                           many=True,
                                           context=context)
        return Response(serializer.data)

    def destroy(self, request, schedule_entry_name):
        raise NotImplemented


class AcquisitionViewSet(MultipleFieldLookupMixin, ViewSet):
    queryset = Acquisition.objects.all()
    serializer_class = AcquisitionSerializer
    lookup_fields = ('schedule_entry_name', 'task_id')
    #download_sigmf_url =

    @detail_route
    def sigmf(self, request, schedule_entry_name, task_id):
        pass
