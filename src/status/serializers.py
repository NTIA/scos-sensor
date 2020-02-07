from rest_framework import serializers

from sensor.utils import convert_string_to_millisecond_iso_format

from .models import Location


class LocationSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        """Change to millisecond datetime format"""
        ret = super().to_representation(instance)
        ret["modified"] = convert_string_to_millisecond_iso_format(ret["modified"])
        return ret

    class Meta:
        model = Location
        exclude = ("id", "active")
