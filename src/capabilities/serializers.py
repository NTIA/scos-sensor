from rest_framework import serializers

from .models import Antenna, Preselector, Receiver, RFPath, SensorDefinition


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


def serialize_array_of_floats(s):
    """Given a string of comma-separated floats, return a list of floats.

    Raises ValidationError if `s` isn't a string of comma-sep'd floats.

    """
    if s is None:
        return

    # Split on commas, clean whitespace, and drop empty strings
    split_values = [x.strip() for x in s.split(',') if x]

    for val in split_values:
        try:
            float(val)
        except ValueError as err:
            raise serializers.ValidationError(str(err))

    return split_values


def validate_array_of_float_field(self, value):
    """Raise ValidationError if value isn't a string of comma-sep'd floats."""
    if not value:
        return value

    split_values = serialize_array_of_floats(value)

    return ', '.join(split_values)


class AntennaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Antenna
        exclude = ('id', )

    def to_representation(self, obj):
        hgains = serialize_array_of_floats(obj.horizontal_gain_pattern)
        vgains = serialize_array_of_floats(obj.vertical_gain_pattern)
        obj.horizontal_gain_pattern = hgains
        obj.vertical_gain_pattern = vgains
        rep = filter_null_fields_and_empty_ararys(self, obj)
        return rep


AntennaSerializer.validate_horizontal_gain_pattern = (
    validate_array_of_float_field)
AntennaSerializer.validate_vertical_gain_pattern = (
    validate_array_of_float_field)


class ReceiverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receiver
        exclude = ('id', )


ReceiverSerializer.to_representation = filter_null_fields


class RFPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFPath
        exclude = ('id', 'signal_condition_unit')


RFPathSerializer.to_representation = filter_null_fields


class PreselectorSerializer(serializers.ModelSerializer):
    rf_path_spec = RFPathSerializer(many=True)

    class Meta:
        model = Preselector
        exclude = ('id', )


PreselectorSerializer.to_representation = (filter_null_fields_and_empty_ararys)


class SensorDefinitionSerializer(serializers.ModelSerializer):
    antenna = AntennaSerializer()
    receiver = ReceiverSerializer()
    preselector = PreselectorSerializer()

    class Meta:
        model = SensorDefinition
        exclude = ('id', )
