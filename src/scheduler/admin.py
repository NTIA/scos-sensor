from django.contrib import admin

from .models import ScheduleEntry


@admin.register(ScheduleEntry)
class ScheduleEntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
