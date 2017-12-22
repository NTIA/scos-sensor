from rest_framework import serializers

from .models import User


class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    """Public user account view."""

    class Meta:
        model = User
        fields = (
            'url',
            'username',
            'is_active',
            'date_joined',
            'last_login',
            'schedule_entries'
        )
        extra_kwargs = {
            'url': {
                'view_name': 'user-detail'
            },
            'is_active': {
                'initial': True
            },
            'schedule_entries': {
                'view_name': 'schedule-detail'
            },
        }
        read_only_fields = (
            'schedule_entries',
            'date_joined',
            'last_login'
        )


class UserDetailsSerializer(UserProfileSerializer):
    """Private user account view."""
    auth_token = serializers.SerializerMethodField()
    has_usable_password = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()

    def get_is_admin(self, obj):
        return obj.is_staff

    class Meta(UserProfileSerializer.Meta):
        fields = UserProfileSerializer.Meta.fields + (
            'email',
            'server_url',
            'auth_token',
            'has_usable_password',
            'is_admin'
        )
        read_only_fields = UserProfileSerializer.Meta.read_only_fields + (
            'auth_token',
        )

    def get_auth_token(self, obj):
        return obj.auth_token.key

    def get_has_usable_password(self, obj):
        return obj.has_usable_password()
