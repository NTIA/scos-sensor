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
            'schedule_entry',
            'acquisitions_available',
            'url'
        )
        extra_kwargs = {
            'url': {
                'view_name': 'v1:acquisitions-preview',
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
    # http://www.django-rest-framework.org/api-guide/relations/#custom-hyperlinked-fields

    def get_url(self, obj, view_name, request, format):
        kw = {
            'schedule_entry_name': obj.schedule_entry.name,
            'task_id': obj.task_id
        }
        return reverse(view_name, kwargs=kw, request=request, format=format)


class AcquisitionPreviewSerializer(serializers.ModelSerializer):
    metadata = AcquisitionHyperlinkedRelatedField(
        view_name='v1:acquisition-metadata',
        read_only=True,
        source='*'  # pass whole object
    )
    data = AcquisitionHyperlinkedRelatedField(
        view_name='v1:acquisition-data',
        read_only=True,
        source='*'  # pass whole object
    )
    metadata_global = serializers.DictField(source='metadata.global',
                                            read_only=True)

    class Meta:
        model = Acquisition
        fields = (
            'task_id',
            'created_at',
            'metadata',
            'data',
            'metadata_global'
        )
        extra_kwargs = {
            'schedule_entry': {
                'view_name': 'v1:schedule-detail',
                'lookup_field': 'name'
            }
        }


class AcquisitionMetadataSerializer(serializers.Serializer):
    def to_representation(self, value):
        return value.metadata
