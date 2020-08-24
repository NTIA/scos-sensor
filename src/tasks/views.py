import logging
import tempfile
from functools import partial

import sigmf.archive
import sigmf.sigmffile
from django.http import FileResponse, Http404
from rest_framework import filters, status
from rest_framework.decorators import action, api_view
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import DestroyModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet

from schedule.models import ScheduleEntry
from scheduler import scheduler
from django.conf import settings

from .models.acquisition import Acquisition
from .models.task_result import TaskResult
from .permissions import IsAdminOrOwnerOrReadOnly
from .serializers.task import TaskSerializer
from .serializers.task_result import TaskResultSerializer, TaskResultsOverviewSerializer
import gpg

PASSPHRASE = settings.PASSPHRASE

logger = logging.getLogger(__name__)


@api_view()
def task_root(request, version, format=None):
    """Provides links to upcoming and completed tasks"""
    reverse_ = partial(reverse, request=request, format=format)
    task_endpoints = {
        "upcoming": reverse_("upcoming-tasks"),
        "completed": reverse_("task-results-overview"),
    }

    return Response(task_endpoints)


@api_view()
def upcoming_tasks(request, version, format=None):
    """Returns a snapshot of upcoming tasks."""
    context = {"request": request}
    taskq = scheduler.thread.task_queue.to_list()[: settings.MAX_TASK_QUEUE]
    taskq_serializer = TaskSerializer(taskq, many=True, context=context)

    return Response(taskq_serializer.data)


class TaskResultsOverviewViewSet(ListModelMixin, GenericViewSet):
    """
    list:
    Returns an overview of how many results are available per schedule
    entry.
    """

    lookup_field = "schedule_entry_name"
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

        filter = {"schedule_entry__name": self.kwargs["schedule_entry_name"]}
        if not self.request.user.is_staff:
            filter.update({"schedule_entry__is_private": False})

        queryset = base_queryset.filter(**filter)

        if not queryset.exists():
            raise Http404

        return queryset

    def get_object(self):
        queryset = self.get_queryset()
        filter = {"task_id": self.kwargs["task_id"]}

        return get_object_or_404(queryset, **filter)


class TaskResultListViewSet(ListModelMixin, GenericViewSet):
    """
    list:
    Returns a list of all results created by the given schedule entry.

    destroy_all:
    Deletes all results created by the given schedule entry.

    archive:
    Downloads the acquisition's SigMF archive.

    """

    queryset = TaskResult.objects.all()
    serializer_class = TaskResultSerializer
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [
        IsAdminOrOwnerOrReadOnly
    ]
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    lookup_fields = ("schedule_entry__name", "task_id")
    ordering_fields = ("task_id", "started", "finished", "duration", "status")
    search_fields = ("task_id", "status", "detail")

    def get_queryset(self):
        # .list() does not call .get_object(), which triggers permissions
        # checks, so we need to filter our queryset based on `is_private` and
        # request user.
        base_queryset = self.filter_queryset(self.queryset)

        filter = {"schedule_entry__name": self.kwargs["schedule_entry_name"]}
        if not self.request.user.is_staff:
            filter.update({"schedule_entry__is_private": False})

        queryset = base_queryset.filter(**filter)

        if not queryset.exists():
            raise Http404
        return queryset.all()

    @action(detail=False, methods=("delete",))
    def destroy_all(self, request, version, schedule_entry_name):
        queryset = self.get_queryset()

        if not queryset.exists():
            raise Http404

        queryset.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False)
    def archive(self, request, version, schedule_entry_name):
        queryset = self.get_queryset()

        acquisitions = Acquisition.objects.filter(task_result__in=queryset)

        if not acquisitions.exists():
            raise Http404

        fname = settings.FQDN + "_" + schedule_entry_name + ".sigmf"

        # FileResponse handles closing the file
        tmparchive = tempfile.TemporaryFile()
        build_sigmf_archive(tmparchive, schedule_entry_name, acquisitions)
        content_type = "application/x-tar"
        response = FileResponse(
            tmparchive, as_attachment=True, filename=fname, content_type=content_type
        )

        return response


class TaskResultInstanceViewSet(
    MultipleFieldLookupMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet
):
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
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [
        IsAdminOrOwnerOrReadOnly
    ]
    lookup_fields = ("schedule_entry__name", "task_id")

    @action(detail=True)
    def archive(self, request, version, schedule_entry_name, task_id):
        entry_name = schedule_entry_name
        fname = settings.FQDN + "_" + entry_name + "_" + str(task_id) + ".sigmf"
        tr = self.get_object()
        acquisitions = Acquisition.objects.filter(task_result=tr)
        if not acquisitions:
            raise Http404

        # FileResponse handles closing the file
        tmparchive = tempfile.TemporaryFile()
        build_sigmf_archive(tmparchive, schedule_entry_name, acquisitions)
        content_type = "application/x-tar"
        response = FileResponse(
            tmparchive, as_attachment=True, filename=fname, content_type=content_type
        )
        return response


def build_sigmf_archive(fileobj, schedule_entry_name, acquisitions):
    """Build a SigMF archive containing `acquisitions` and save to fileobj.

    @param fileobj: a fileobj open for writing
    @param schedule_entry_name: the name of the parent schedule entry
    @param acquisitions: an iterable of Acquisition objects from the database
    @return: None

    """
    logger.debug("building sigmf archive")

    multirecording = len(acquisitions) > 1

    for acq in acquisitions:
        with tempfile.NamedTemporaryFile(delete=True) as tmpdata:
            if acq.data_encrypted:
                gpg.Context().decrypt(acq.data.read(), sink=tmpdata, passphrase=PASSPHRASE)
            else:
                tmpdata.write(acq.data.read())
            tmpdata.seek(0)  # move fd ptr to start of data for reading
            name = schedule_entry_name + "_" + str(acq.task_result.task_id)
            if multirecording:
                name += "-" + str(acq.recording_id)
            sigmf_file = sigmf.sigmffile.SigMFFile(metadata=acq.metadata, name=name)
            sigmf_file.set_data_file(tmpdata.name)

            sigmf.archive.SigMFArchive(sigmf_file, path=name, fileobj=fileobj)

    logger.debug("sigmf archive built")
