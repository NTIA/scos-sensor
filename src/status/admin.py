# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('longitude', 'latitude')
