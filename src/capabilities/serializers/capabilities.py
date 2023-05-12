from rest_framework import serializers

from .ntia_sensor import SensorSerializer


class ActionInfoSerializer(serializers.Serializer):
    name = serializers.CharField()
    summary = serializers.CharField()
    description = serializers.CharField()


class CapabilitiesSerializer(serializers.Serializer):
    sensor = SensorSerializer(many=False)
    actions = ActionInfoSerializer(many=True)
