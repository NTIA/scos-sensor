from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
from rest_framework.reverse import reverse

from schedule.models import ScheduleEntry
from schedule.serializers import ISOMillisecondDateTimeFormatField
from sensor import V1
from tasks.models import Acquisition, TaskResult

from .acquisition import AcquisitionSerializer


class TaskResultHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):
    # django-rest-framework.org/api-guide/relations/#custom-hyperlinked-fields
    def get_url(self, obj, view_name, request, format):
        kws = {"schedule_entry_name": obj.schedule_entry.name, "task_id": obj.task_id}
        kws.update(V1)
        url = reverse(view_name, kwargs=kws, request=request, format=format)
        return url


class TaskResultsOverviewSerializer(serializers.HyperlinkedModelSerializer):
    archive = serializers.SerializerMethodField(
        help_text="The link to a multi-recording archive of all available acquisitions"
    )
    task_results = serializers.SerializerMethodField(
        help_text="The link to the task results"
    )
    task_results_available = serializers.SerializerMethodField(
        help_text="The number of available results"
    )
    schedule_entry = serializers.SerializerMethodField(
        help_text="The related schedule entry for the result"
    )

    class Meta:
        model = ScheduleEntry
        fields = ("archive", "task_results", "task_results_available", "schedule_entry")

    def get_archive(self, obj) -> OpenApiTypes.URI:
        # FIXME: This query can almost certiainly be optimized
        acquisitions_available = Acquisition.objects.filter(
            task_result__in=obj.task_results.all()
        ).exists()

        if not acquisitions_available:
            return None

        request = self.context["request"]
        route = "task-result-list-archive"
        kws = {"schedule_entry_name": obj.name}
        kws.update(V1)
        url = reverse(route, kwargs=kws, request=request)
        return url

    def get_task_results(self, obj) -> OpenApiTypes.URI:
        request = self.context["request"]
        route = "task-result-list"
        kws = {"schedule_entry_name": obj.name}
        kws.update(V1)
        url = reverse(route, kwargs=kws, request=request)
        return url

    def get_task_results_available(self, obj) -> OpenApiTypes.INT:
        return obj.task_results.count()

    def get_schedule_entry(self, obj) -> OpenApiTypes.URI:
        request = self.context["request"]
        route = "schedule-detail"
        kws = {"pk": obj.name}
        kws.update(V1)
        url = reverse(route, kwargs=kws, request=request)
        return url


class TaskResultSerializer(serializers.HyperlinkedModelSerializer):
    self = TaskResultHyperlinkedRelatedField(
        view_name="task-result-detail",
        read_only=True,
        help_text="The url of the result",
        source="*",  # pass whole object
    )
    schedule_entry = serializers.SerializerMethodField(
        help_text="The url of the parent schedule entry"
    )
    data = AcquisitionSerializer(many=True)
    started = ISOMillisecondDateTimeFormatField(help_text="The time the task started")
    finished = ISOMillisecondDateTimeFormatField(help_text="The time the task finished")

    class Meta:
        model = TaskResult
        fields = (
            "self",
            "schedule_entry",
            "task_id",
            "status",
            "detail",
            "started",
            "finished",
            "duration",
            "data",
        )

    def get_schedule_entry(self, obj) -> OpenApiTypes.URI:
        request = self.context["request"]
        route = "schedule-detail"
        kws = {"pk": obj.schedule_entry.name}
        kws.update(V1)
        url = reverse(route, kwargs=kws, request=request)

        return url
