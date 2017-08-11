from rest_framework import serializers

from .models import User


class UserSerializer(serializers.HyperlinkedModelSerializer):
    auth_token = serializers.SerializerMethodField()
    has_usable_password = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'url',
            'username',
            'email',
            'server_url',
            'auth_token',
            'has_usable_password',
            'is_active',
            'is_admin',
            'date_joined',
            'last_login',
            'schedule_entries'
        )
        extra_kwargs = {
            'is_active': {
                'initial': True
            },
            'schedule_entries': {
                'view_name': 'v1:schedule-detail',
                'lookup_field': 'name'
            },
        }
        read_only_fields = (
            'auth_token',
            'schedule_entries',
            'date_joined',
            'last_login'
        )

    def get_auth_token(self, obj):
        return obj.auth_token.key

    def get_has_usable_password(self, obj):
        return obj.has_usable_password()
