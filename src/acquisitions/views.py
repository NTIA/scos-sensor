import tempfile

from django.core.files import File
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import list_route, detail_route
from rest_framework.mixins import (ListModelMixin,
                                   RetrieveModelMixin,
                                   DestroyModelMixin)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

import sigmf.sigmffile

from schedule.models import ScheduleEntry
from .models import Acquisition
from .serializers import (AcquisitionsOverviewSerializer,
                          AcquisitionSerializer)


class AcquisitionsOverviewViewSet(ListModelMixin, GenericViewSet):
    lookup_field = 'schedule_entry_name'
    queryset = ScheduleEntry.objects.all()
    serializer_class = AcquisitionsOverviewSerializer


class MultipleFieldLookupMixin(object):
    """Get multiple field filtering based on a `lookup_fields` attribute."""
    def get_queryset(self):
        base_queryset = super(MultipleFieldLookupMixin, self).get_queryset()
        base_queryset = self.filter_queryset(base_queryset)
        filter = {'schedule_entry__name': self.kwargs['schedule_entry_name']}
        queryset = base_queryset.filter(**filter)
        if not queryset.exists():
            raise Http404

        return queryset

    def get_object(self):
        queryset = self.get_queryset()
        filter = {'task_id': self.kwargs['task_id']}
        return get_object_or_404(queryset, **filter)


class AcquisitionListViewSet(MultipleFieldLookupMixin,
                             ListModelMixin,
                             GenericViewSet):
    queryset = Acquisition.objects.all()
    serializer_class = AcquisitionSerializer
    lookup_fields = ('schedule_entry__name', 'task_id')

    @list_route(methods=('DELETE',))
    def destroy_all(self, request, schedule_entry_name):
        queryset = self.get_queryset()
        queryset = queryset.filter(schedule_entry__name=schedule_entry_name)
        if not queryset.exists():
            raise Http404
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AcquisitionInstanceViewSet(MultipleFieldLookupMixin,
                                 RetrieveModelMixin,
                                 DestroyModelMixin,
                                 GenericViewSet):
    queryset = Acquisition.objects.all()
    serializer_class = AcquisitionSerializer
    lookup_fields = ('schedule_entry__name', 'task_id')

    @detail_route()
    def archive(self, request, schedule_entry_name, task_id):
        entry_name = schedule_entry_name
        acq = self.get_object()

        with tempfile.NamedTemporaryFile() as tempdatafile:
            tempdatafile.write(acq.data)
            tempdatafile.seek(0)  # move fd ptr to start of data for reading

            sigmf_file = sigmf.sigmffile.SigMFFile(metadata=acq.sigmf_metadata)
            sigmf_file.set_data_file(tempdatafile.name)

            with tempfile.TemporaryFile() as t:
                # FIXME: prefix filename with sensor_id when that is available
                filename = entry_name + '_' + str(task_id) + '.sigmf'
                sigmf_file.archive(name=filename, fileobj=t)
                content_type = 'application/x-tar'
                response = HttpResponse(File(t), content_type=content_type)
                content_disp = 'attachment; filename="{}"'.format(filename)
                response['Content-Disposition'] = content_disp
                return response
