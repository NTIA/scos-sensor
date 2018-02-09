from rest_framework import serializers
from rest_framework.reverse import reverse

from sensor import V1
from .models import User


class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    """Public user account view."""
    schedule_entries = serializers.SerializerMethodField(
        help_text="The list of schedule entries owned by the user"
    )

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

    def get_schedule_entries(self, obj):
        """Filter private schedule entries if requester is not an admin."""
        request = self.context['request']
        entries = obj.schedule_entries.get_queryset()
        if not request.user.is_staff:
            entries = entries.filter(is_private=False)

        urls = []
        for entry in entries:
            route = 'schedule-detail'
            kws = {'pk': entry.name}
            kws.update(V1)
            urls.append(reverse(route, kwargs=kws, request=request))

        return urls


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
