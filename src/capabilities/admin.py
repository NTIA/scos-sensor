# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import (
    Antenna,
    Preselector,
    Receiver,
    RFPath,
    SensorDefinition
)


@admin.register(Antenna)
class AntennaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'model',
        'type',
        'low_frequency',
        'high_frequency',
        'gain',
        'cable_loss',
    )


@admin.register(Receiver)
class ReceiverAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'model',
        'low_frequency',
        'high_frequency',
        'noise_figure',
        'max_power',
    )


@admin.register(RFPath)
class RFPathAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'preselector',
        'rf_path_number',
        'low_frequency_passband',
        'high_frequency_passband',
    )
    list_filter = ('preselector',)


@admin.register(Preselector)
class PreselectorAdmin(admin.ModelAdmin):
    list_display = ('id',)


@admin.register(SensorDefinition)
class SensorDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'host_controller',
        'antenna',
        'preselector',
        'receiver',
    )
