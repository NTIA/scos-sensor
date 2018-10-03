import tempfile

from django.core.files import File
from django.http import Http404, HttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import (ListModelMixin, RetrieveModelMixin,
                                   DestroyModelMixin)
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet

import sigmf.sigmffile

from schedule.models import ScheduleEntry
from .models import Acquisition
from .permissions import IsAdminOrOwnerOrReadOnly
from .serializers import (AcquisitionsOverviewSerializer,
                          AcquisitionSerializer)


class AcquisitionsOverviewViewSet(ListModelMixin, GenericViewSet):
    """
    list:
    Returns an overview of how many acquisitions are available per schedule
    entry.
    """
    lookup_field = 'schedule_entry_name'
    queryset = ScheduleEntry.objects.all()
    serializer_class = AcquisitionsOverviewSerializer

    def get_queryset(self):
        # .list() does not call .get_object(), which triggers permissions
        # checks, so we need to filter our queryset based on `is_private` and
        # request user.
        base_queryset = self.filter_queryset(self.queryset)
        if self.request.user.is_staff:
            return base_queryset
        else:
            return base_queryset.filter(is_private=False)


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


class AcquisitionListViewSet(MultipleFieldLookupMixin, ListModelMixin,
                             GenericViewSet):
    """
    list:
    Returns a list of all acquisitions created by the given schedule entry.

    destroy_all:
    Deletes all acquisitions created by the given schedule entry.
    """
    queryset = Acquisition.objects.all()
    serializer_class = AcquisitionSerializer
    permission_classes = (
        api_settings.DEFAULT_PERMISSION_CLASSES + [IsAdminOrOwnerOrReadOnly])
    lookup_fields = ('schedule_entry__name', 'task_id')

    @action(detail=False, methods=('delete', ))
    def destroy_all(self, request, version, schedule_entry_name):
        queryset = self.get_queryset()
        queryset = queryset.filter(schedule_entry__name=schedule_entry_name)

        if not queryset.exists():
            raise Http404

        queryset.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class AcquisitionInstanceViewSet(MultipleFieldLookupMixin, RetrieveModelMixin,
                                 DestroyModelMixin, GenericViewSet):
    """
    destroy:
    Deletes the specified acquisition.

    retrieve:
    Returns all available metadata about an acquisition.

    archive:
    Downloads the acquisition's SigMF archive.
    """
    queryset = Acquisition.objects.all()
    serializer_class = AcquisitionSerializer
    permission_classes = (
        api_settings.DEFAULT_PERMISSION_CLASSES + [IsAdminOrOwnerOrReadOnly])
    lookup_fields = ('schedule_entry__name', 'task_id')

    @action(detail=True)
    def archive(self, request, version, schedule_entry_name, task_id):
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
