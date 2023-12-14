from rest_framework import serializers


class ApiRootSerializer(serializers.Serializer):
    capabilities = serializers.URLField()
    schedule = serializers.URLField()
    status = serializers.URLField()
    tasks = serializers.URLField()
    users = serializers.URLField()
