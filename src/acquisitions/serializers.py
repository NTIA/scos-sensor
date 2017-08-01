from rest_framework import serializers
from rest_framework.reverse import reverse

from schedule.models import ScheduleEntry
from .models import Acquisition


class AcquisitionsOverviewSerializer(serializers.HyperlinkedModelSerializer):
    schedule_entry_name = serializers.SerializerMethodField()
    acquisitions_available = serializers.SerializerMethodField()
    schedule_entry_url = serializers.SerializerMethodField()

    class Meta:
        model = ScheduleEntry
        fields = (
            'schedule_entry_name',
            'acquisitions_available',
            'created_at',
            'schedule_entry_url',
            'url'
        )
        extra_kwargs = {
            'url': {
                'view_name': 'v1:acquisitions-detail',
                'lookup_field': 'name'
            }
        }

    def get_acquisitions_available(self, obj):
        return obj.acquisitions.count()

    def get_schedule_entry_name(self, obj):
        return obj.name

    def get_schedule_entry_url(self, obj):
        request = self.context['request']
        return reverse('v1:schedule-detail', args=(obj.name,), request=request)


class AcquisitionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Acquisition
        fields = '__all__'

        extra_kwargs = {
            'url': {
                'view_name': 'v1:acquisitions-metadata',
                'lookup_field': 'schedule_entry_name'
            }
        }
