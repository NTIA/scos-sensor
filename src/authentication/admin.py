"""Register admin page for custom User."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class SensorUserAdmin(UserAdmin):
    model = User

    fieldsets = UserAdmin.fieldsets + (
        # server_url unforunately gets placed at bottom of User admin page
        (None, {
            'fields': ('server_url', )
        }), )


admin.site.register(User, SensorUserAdmin)
