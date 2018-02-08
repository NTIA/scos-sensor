from rest_framework import serializers
from rest_framework.reverse import reverse

from schedule.models import ScheduleEntry
from sensor import V1
from .models import TaskResult


class TaskResultsOverviewSerializer(serializers.HyperlinkedModelSerializer):
    schedule_entry = serializers.SerializerMethodField(
        help_text="The related schedule entry for the result"
    )
    results_available = serializers.SerializerMethodField(
        help_text="The number of available results"
    )

    class Meta:
        model = ScheduleEntry
        fields = (
            'url',
            'results_available',
            'schedule_entry'
        )
        extra_kwargs = {
            'url': {
                'view_name': 'result-list',
                'lookup_field': 'name',
                'lookup_url_kwarg': 'schedule_entry_name',
                'help_text': 'The url of the list of results'
            }
        }

    def get_results_available(self, obj):
        return obj.results.count()

    def get_schedule_entry(self, obj):
        request = self.context['request']
        kwargs = {'pk': obj.name}
        return reverse('schedule-detail', kwargs=kwargs, request=request)


# FIXME: this is identical to AcquisitionHyperlinkedRelatedField
class TaskResultHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):
    # django-rest-framework.org/api-guide/relations/#custom-hyperlinked-fields
    def get_url(self, obj, view_name, request, format):
        kws = {
            'schedule_entry_name': obj.schedule_entry.name,
            'task_id': obj.task_id
        }
        kws.update(V1)
        return reverse(view_name, kwargs=kws, request=request, format=format)


class TaskResultSerializer(serializers.ModelSerializer):
    url = TaskResultHyperlinkedRelatedField(
        view_name='result-detail',
        read_only=True,
        help_text="The url of the result",
        source='*'  # pass whole object
    )

    class Meta:
        model = TaskResult
        fields = (
            'url',
            'task_id',
            'started',
            'finished',
            'duration',
            'result',
            'detail'
        )
        extra_kwargs = {
            'schedule_entry': {
                'view_name': 'schedule-detail',
                'lookup_field': 'name'
            }
        }
