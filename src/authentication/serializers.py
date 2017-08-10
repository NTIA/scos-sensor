from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    auth_token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'url',
            'username',
            'password',
            'auth_token',
            'schedule_entries'
        )
        extra_kwargs = {
            'schedule_entries': {
                'view_name': 'v1:schedule-detail',
                'lookup_field': 'name'
            },
            'password': {
                'style': {
                    'input_type': 'password'
                },
                'write_only': True
            }
        }
        read_only_fields = ('auth_token', 'schedule_entries')

    def get_auth_token(self, obj):
        return obj.auth_token.key
