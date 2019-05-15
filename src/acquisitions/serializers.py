from rest_framework import serializers
from rest_framework.reverse import reverse

from schedule.models import ScheduleEntry
from sensor import V1
from .models import Acquisition


class AcquisitionsOverviewSerializer(serializers.HyperlinkedModelSerializer):
    results = serializers.SerializerMethodField(
        help_text="The link to the acquisitions")
    schedule_entry = serializers.SerializerMethodField(
        help_text="The related schedule entry for the acquisition")
    acquisitions_available = serializers.SerializerMethodField(
        help_text="The number of available acquisitions")
    archive = serializers.SerializerMethodField(
        help_text="The url to download a SigMF archive of all acquisitions"
    )

    class Meta:
        model = ScheduleEntry
        fields = ('results', 'acquisitions_available', 'archive',
                  'schedule_entry')

    def get_results(self, obj):
        request = self.context['request']
        route = 'acquisition-list'
        kws = {'schedule_entry_name': obj.name}
        kws.update(V1)
        url = reverse(route, kwargs=kws, request=request)
        return url

    def get_acquisitions_available(self, obj):
        return obj.acquisitions.count()

    def get_schedule_entry(self, obj):
        request = self.context['request']
        kwargs = {'pk': obj.name}
        url = reverse('schedule-detail', kwargs=kwargs, request=request)
        return url

    def get_archive(self, obj):
        request = self.context['request']
        kwargs = {'schedule_entry_name': obj.name}
        url = reverse('acquisition-list-archive', kwargs=kwargs,
                      request=request)
        return url


class AcquisitionHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):
    # django-rest-framework.org/api-guide/relations/#custom-hyperlinked-fields
    def get_url(self, obj, view_name, request, format):
        kws = {
            'schedule_entry_name': obj.schedule_entry.name,
            'task_id': obj.task_id
        }
        kws.update(V1)
        url = reverse(view_name, kwargs=kws, request=request, format=format)
        return url


class AcquisitionSerializer(serializers.ModelSerializer):
    # `self` here refers to the self url field - this seems to work
    self = AcquisitionHyperlinkedRelatedField(
        view_name='acquisition-detail',
        read_only=True,
        help_text="The url of the acquisition",
        source='*'  # pass whole object
    )
    archive = AcquisitionHyperlinkedRelatedField(
        view_name='acquisition-archive',
        read_only=True,
        help_text="The url to download a SigMF archive of this acquisition",
        source='*'  # pass whole object
    )
    sigmf_metadata = serializers.DictField(
        help_text="The sigmf meta data for the acquisition")

    class Meta:
        model = Acquisition
        fields = ('self', 'task_id', 'created', 'archive', 'sigmf_metadata')
        extra_kwargs = {
            'schedule_entry': {
                'view_name': 'schedule-detail',
                'lookup_field': 'name'
            }
        }
