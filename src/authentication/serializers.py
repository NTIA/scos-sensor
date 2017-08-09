from django.contrib.auth.models import User, Group
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups', 'schedule_entries')
        extra_kwargs = {
            'schedule_entries': {
                'view_name': 'v1:schedule-detail',
                'lookup_field': 'name'
            }
        }
        read_only_fields = ('schedule_entries',)


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')
