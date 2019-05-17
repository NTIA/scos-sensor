import logging
import tempfile

from django.http import Http404, FileResponse
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import (
    ListModelMixin, RetrieveModelMixin, DestroyModelMixin)
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet

import sigmf.archive
import sigmf.sigmffile

import sensor.settings
from schedule.models import ScheduleEntry
from .models.task_result import TaskResult
from .permissions import IsAdminOrOwnerOrReadOnly
from .serializers.task_result import (
    TaskResultsOverviewSerializer, TaskResultSerializer)


logger = logging.getLogger(__name__)


class ResultsOverviewViewSet(ListModelMixin, GenericViewSet):
    """
    list:
    Returns an overview of how many results are available per schedule
    entry.
    """
    lookup_field = 'schedule_entry_name'
    queryset = ScheduleEntry.objects.all()
    serializer_class = TaskResultsOverviewSerializer

    def get_queryset(self):
        # .list() does not call .get_object(), which triggers permissions
        # checks, so we need to filter our queryset based on `is_private` and
        # request user.
        base_queryset = self.filter_queryset(self.queryset)
        if self.request.user.is_staff:
            return base_queryset.all()
        else:
            return base_queryset.filter(is_private=False)


class MultipleFieldLookupMixin(object):
    """Get multiple field filtering based on a `lookup_fields` attribute."""

    def get_queryset(self):
        base_queryset = super(MultipleFieldLookupMixin, self).get_queryset()
        base_queryset = self.filter_queryset(base_queryset)

        filter = {'schedule_entry__name': self.kwargs['schedule_entry_name']}
        if not self.request.user.is_staff:
            filter.update({'schedule_entry__is_private': False})

        queryset = base_queryset.filter(**filter)

        if not queryset.exists():
            raise Http404

        return queryset

    def get_object(self):
        queryset = self.get_queryset()
        filter = {'task_id': self.kwargs['task_id']}

        return get_object_or_404(queryset, **filter)


class TaskResultListViewSet(MultipleFieldLookupMixin, ListModelMixin,
                            GenericViewSet):
    """
    list:
    Returns a list of all acquisitions created by the given schedule entry.

    destroy_all:
    Deletes all acquisitions created by the given schedule entry.
    """
    queryset = TaskResult.objects.all()
    serializer_class = TaskResultSerializer
    permission_classes = (
        api_settings.DEFAULT_PERMISSION_CLASSES + [IsAdminOrOwnerOrReadOnly])
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    lookup_fields = ('schedule_entry__name', 'task_id')
    ordering_fields = ('task_id', 'created')
    search_fields = ('sigmf_metadata', )

    @action(detail=False, methods=('delete', ))
    def destroy_all(self, request, version, schedule_entry_name):
        queryset = self.get_queryset()
        queryset = queryset.filter(schedule_entry__name=schedule_entry_name)

        if not queryset.exists():
            raise Http404

        queryset.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False)
    def archive(self, request, version, schedule_entry_name):
        queryset = self.get_queryset()
        queryset = queryset.filter(schedule_entry__name=schedule_entry_name)
        fqdn = sensor.settings.FQDN
        fname = fqdn + '_' + schedule_entry_name + '.sigmf'

        if not queryset.exists():
            raise Http404

        # FileResponse handles closing the file
        tmparchive = tempfile.TemporaryFile()
        build_sigmf_archive(tmparchive, schedule_entry_name, queryset)
        content_type = 'application/x-tar'
        response = FileResponse(tmparchive, as_attachment=True, filename=fname,
                                content_type=content_type)
        return response


class ResultListViewSet(ListModelMixin, GenericViewSet):
    """
    list:
    Returns a list of all results created by the given schedule entry.

    destroy_all:
    Deletes all results created by the given schedule entry.

    """
    queryset = TaskResult.objects.all()
    serializer_class = TaskResultSerializer
    permission_classes = (
        api_settings.DEFAULT_PERMISSION_CLASSES + [IsAdminOrOwnerOrReadOnly])
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    lookup_fields = ('schedule_entry__name', 'task_id')
    ordering_fields = ('task_id', 'started', 'finished', 'duration', 'result')
    search_fields = ('task_id', 'result', 'detail')

    def get_queryset(self):
        # .list() does not call .get_object(), which triggers permissions
        # checks, so we need to filter our queryset based on `is_private` and
        # request user.
        base_queryset = self.filter_queryset(self.queryset)

        filter = {'schedule_entry__name': self.kwargs['schedule_entry_name']}
        if not self.request.user.is_staff:
            filter.update({'schedule_entry__is_private': False})

        queryset = base_queryset.filter(**filter)

        if not queryset.exists():
            raise Http404

        return queryset.all()

    @action(detail=False, methods=('delete', ))
    def destroy_all(self, request, version, schedule_entry_name):
        queryset = self.get_queryset()

        if not queryset.exists():
            raise Http404

        queryset.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False)
    def archive(self, request, version, schedule_entry_name):
        queryset = self.get_queryset()

        if not queryset.exists():
            raise Http404

        fqdn = sensor.settings.FQDN
        fname = fqdn + '_' + schedule_entry_name + '.sigmf'

        # FileResponse handles closing the file
        tmparchive = tempfile.TemporaryFile()
        build_sigmf_archive(tmparchive, schedule_entry_name, queryset)
        content_type = 'application/x-tar'
        response = FileResponse(tmparchive, as_attachment=True, filename=fname,
                                content_type=content_type)

        return response


class ResultInstanceViewSet(MultipleFieldLookupMixin, RetrieveModelMixin,
                            DestroyModelMixin, GenericViewSet):
    """
    retrieve:
    Returns a specific result.

    destroy:
    Deletes the specified acquisition.

    archive:
    Downloads the acquisition's SigMF archive.

    """
    queryset = TaskResult.objects.all()
    serializer_class = TaskResultSerializer
    permission_classes = (
        api_settings.DEFAULT_PERMISSION_CLASSES + [IsAdminOrOwnerOrReadOnly])
    lookup_fields = ('schedule_entry__name', 'task_id')

    @action(detail=True)
    def archive(self, request, version, schedule_entry_name, task_id):
        entry_name = schedule_entry_name
        fqdn = sensor.settings.FQDN
        fname = fqdn + '_' + entry_name + '_' + str(task_id) + '.sigmf'
        acq = self.get_object()

        # FileResponse handles closing the file
        tmparchive = tempfile.TemporaryFile()
        build_sigmf_archive(tmparchive, schedule_entry_name, [acq])
        content_type = 'application/x-tar'
        response = FileResponse(tmparchive, as_attachment=True, filename=fname,
                                content_type=content_type)
        return response


def build_sigmf_archive(fileobj, schedule_entry_name, acquisitions):
    """Build a SigMF archive containing `acquisitions` and save to fileobj.

    @param fileobj: a fileobj open for writing
    @param schedule_entry_name: the name of the parent schedule entry
    @param acquisitions: an iterable of Acquisition objects from the database
    @return: None

    """
    logger.debug("building sigmf archive")

    for acq in acquisitions:
        with tempfile.NamedTemporaryFile() as tmpdata:
            tmpdata.write(acq.data)
            tmpdata.seek(0)  # move fd ptr to start of data for reading
            name = schedule_entry_name + '_' + str(acq.task_id)
            sigmf_file = sigmf.sigmffile.SigMFFile(metadata=acq.sigmf_metadata,
                                                   name=name)
            sigmf_file.set_data_file(tmpdata.name)

            sigmf.archive.SigMFArchive(sigmf_file, path=name, fileobj=fileobj)

    logger.debug("sigmf archive built")
