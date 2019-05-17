from rest_framework import serializers
from rest_framework.reverse import reverse

from schedule.models import ScheduleEntry
from sensor import V1
from results.models import TaskResult

from .acquisition import AcquisitionSerializer


class TaskResultHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):
    # django-rest-framework.org/api-guide/relations/#custom-hyperlinked-fields
    def get_url(self, obj, view_name, request, format):
        kws = {
            'schedule_entry_name': obj.schedule_entry.name,
            'task_id': obj.task_id
        }
        kws.update(V1)
        url = reverse(view_name, kwargs=kws, request=request, format=format)
        return url


class TaskResultsOverviewSerializer(serializers.HyperlinkedModelSerializer):
    results = serializers.SerializerMethodField(
        help_text="The link to the task results")
    schedule_entry = serializers.SerializerMethodField(
        help_text="The related schedule entry for the result")
    results_available = serializers.SerializerMethodField(
        help_text="The number of available results")

    class Meta:
        model = ScheduleEntry
        fields = ('results', 'results_available', 'schedule_entry')

    def get_results(self, obj):
        request = self.context['request']
        route = 'result-list'
        kws = {'schedule_entry_name': obj.name}
        kws.update(V1)
        url = reverse(route, kwargs=kws, request=request)
        return url

    def get_results_available(self, obj):
        return obj.results.count()

    def get_schedule_entry(self, obj):
        request = self.context['request']
        route = 'schedule-detail'
        kws = {'pk': obj.name}
        kws.update(V1)
        url = reverse(route, kwargs=kws, request=request)
        return url


class TaskResultSerializer(serializers.HyperlinkedModelSerializer):
    self = TaskResultHyperlinkedRelatedField(
        view_name='result-detail',
        read_only=True,
        help_text="The url of the result",
        source='*'  # pass whole object
    )
    schedule_entry = serializers.SerializerMethodField(
        help_text="The url of the parent schedule entry")
    data = AcquisitionSerializer(many=True)

    class Meta:
        model = TaskResult
        fields = (
            'self',
            'schedule_entry',
            'task_id',
            'status',
            'detail',
            'started',
            'finished',
            'duration',
            'data'
        )

    def get_schedule_entry(self, obj):
        request = self.context['request']
        route = 'schedule-detail'
        kws = {'pk': obj.schedule_entry.name}
        kws.update(V1)
        url = reverse(route, kwargs=kws, request=request)

        return url
