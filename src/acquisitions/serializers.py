from rest_framework import serializers
from rest_framework.reverse import reverse

from schedule.models import ScheduleEntry
from .models import Acquisition


class AcquisitionsOverviewSerializer(serializers.HyperlinkedModelSerializer):
    schedule_entry = serializers.SerializerMethodField()
    acquisitions_available = serializers.SerializerMethodField()

    class Meta:
        model = ScheduleEntry
        fields = (
            'url',
            'acquisitions_available',
            'schedule_entry'
        )
        extra_kwargs = {
            'url': {
                'view_name': 'v1:acquisition-list',
                'lookup_field': 'name',
                'lookup_url_kwarg': 'schedule_entry_name'
            }
        }

    def get_acquisitions_available(self, obj):
        return obj.acquisitions.count()

    def get_schedule_entry(self, obj):
        request = self.context['request']
        return reverse('v1:schedule-detail', args=(obj.name,), request=request)


class AcquisitionHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):
    # django-rest-framework.org/api-guide/relations/#custom-hyperlinked-fields
    def get_url(self, obj, view_name, request, format):
        kws = {
            'schedule_entry_name': obj.schedule_entry.name,
            'task_id': obj.task_id
        }
        return reverse(view_name, kwargs=kws, request=request, format=format)


class AcquisitionSerializer(serializers.ModelSerializer):
    url = AcquisitionHyperlinkedRelatedField(
        view_name='v1:acquisition-detail',
        read_only=True,
        source='*'  # pass whole object
    )
    archive = AcquisitionHyperlinkedRelatedField(
        view_name='v1:acquisition-archive',
        read_only=True,
        source='*'  # pass whole object
    )
    sigmf_metadata = serializers.DictField()

    class Meta:
        model = Acquisition
        fields = (
            'url',
            'task_id',
            'created',
            'archive',
            'sigmf_metadata'
        )
        extra_kwargs = {
            'schedule_entry': {
                'view_name': 'v1:schedule-detail',
                'lookup_field': 'name'
            }
        }
