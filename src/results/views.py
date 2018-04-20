from django.http import Http404
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

from schedule.models import ScheduleEntry
from .models import TaskResult
from .serializers import TaskResultsOverviewSerializer, TaskResultSerializer


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


class ResultListViewSet(ListModelMixin, GenericViewSet):
    """
    list:
    Returns a list of all results created by the given schedule entry.
    """
    queryset = TaskResult.objects.all()
    serializer_class = TaskResultSerializer
    lookup_fields = ('schedule_entry__name',)

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


class ResultInstanceViewSet(MultipleFieldLookupMixin,
                            RetrieveModelMixin,
                            GenericViewSet):
    """
    retrieve:
    Returns a specific result.
    """
    queryset = TaskResult.objects.all()
    serializer_class = TaskResultSerializer
    lookup_fields = ('schedule_entry__name', 'task_id')
