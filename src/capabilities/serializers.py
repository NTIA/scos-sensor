from rest_framework import serializers

from .models import (
    Antenna,
    DataExtractionUnit,
    RFPath,
    SensorDefinition,
    SignalConditioningUnit
)


def filter_null_fields(self, obj):
    rep = super(self.__class__, self).to_representation(obj)
    for k, v in rep.items():
        if v is None:
            del rep[k]

    return rep


def filter_null_fields_and_empty_ararys(self, obj):
    rep = filter_null_fields(self, obj)
    empty_list = []
    for k, v in rep.items():
        if v == empty_list:
            del rep[k]

    return rep


class AntennaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Antenna
        exclude = ('id',)


AntennaSerializer.to_representation = filter_null_fields_and_empty_ararys


class DataExtractionUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataExtractionUnit
        exclude = ('id',)


DataExtractionUnitSerializer.to_representation = filter_null_fields


class RFPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFPath
        exclude = ('id', 'signal_condition_unit')


RFPathSerializer.to_representation = filter_null_fields


class SignalConditioningUnitSerializer(serializers.ModelSerializer):
    rf_path_spec = RFPathSerializer(many=True)

    class Meta:
        model = SignalConditioningUnit
        exclude = ('id',)


SignalConditioningUnitSerializer.to_representation = (
    filter_null_fields_and_empty_ararys
)


class SensorDefinitionSerializer(serializers.ModelSerializer):
    antenna = AntennaSerializer()
    data_extraction_unit = DataExtractionUnitSerializer()
    signal_condition_unit = SignalConditioningUnitSerializer()

    class Meta:
        model = SensorDefinition
        exclude = ('id',)
