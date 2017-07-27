from rest_framework import serializers

from .models import Acquisition


class AcquisitionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Acquisition
        fields = '__all__'
