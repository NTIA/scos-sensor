# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import (
    Antenna,
    DataExtractionUnit,
    RFPath,
    SensorDefinition,
    SignalConditioningUnit
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


@admin.register(DataExtractionUnit)
class DataExtractionUnitAdmin(admin.ModelAdmin):
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
        'signal_condition_unit',
        'rf_path_number',
        'low_frequency_passband',
        'high_frequency_passband',
    )
    list_filter = ('signal_condition_unit',)


@admin.register(SignalConditioningUnit)
class SignalConditioningUnitAdmin(admin.ModelAdmin):
    list_display = ('id',)


@admin.register(SensorDefinition)
class SensorDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'host_controller',
        'antenna',
        'signal_condition_unit',
        'data_extraction_unit',
    )
