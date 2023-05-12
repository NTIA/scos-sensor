from rest_framework import serializers


class HardwareSpecSerializer(serializers.Serializer):
    id = serializers.CharField(required=False)
    model = serializers.CharField(required=False)
    version = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    supplemental_information = serializers.CharField(required=False)


class AmplifierSerializer(serializers.Serializer):
    amplifier_spec = HardwareSpecSerializer(required=False)
    gain = serializers.FloatField(required=False)
    noise_figure = serializers.FloatField(required=False)
    max_power = serializers.FloatField(required=False)


class AntennaSerializer(serializers.Serializer):
    antenna_spec = HardwareSpecSerializer(required=True)
    type = serializers.CharField(required=False)
    frequency_low = serializers.FloatField(required=False)
    frequency_high = serializers.FloatField(required=False)
    polarization = serializers.CharField(required=False)
    cross_polar_discrimination = serializers.FloatField(required=False)
    gain = serializers.FloatField(required=False)
    horizontal_gain_pattern = serializers.ListField(
        child=serializers.FloatField(), required=False
    )
    vertical_gain_pattern = serializers.ListField(
        child=serializers.FloatField(), required=False
    )
    horizontal_beamwidth = serializers.FloatField(required=False)
    vertical_beamwidth = serializers.FloatField(required=False)
    voltage_standing_wave_ratio = serializers.FloatField(required=False)
    cable_loss = serializers.FloatField(required=False)
    steerable = serializers.BooleanField(required=False)
    azimuth_angle = serializers.FloatField(required=False)
    elevation_angle = serializers.FloatField(required=False)


class CalSourceSerializer(serializers.Serializer):
    cal_source_spe = HardwareSpecSerializer(required=False)
    _type = serializers.CharField(required=False)
    enr = serializers.FloatField(required=False)

    def get_fields(self):
        result = super().get_fields()
        # Rename "_type" to "type"
        _type = result.pop("_type")
        result["type"] = _type
        return result


class EnvironmentSerializer(serializers.Serializer):
    category = serializers.CharField(required=False)
    temperature = serializers.FloatField(required=False)
    humidity = serializers.FloatField(required=False)
    weather = serializers.CharField(required=False)
    description = serializers.CharField(required=False)


class FilterSerializer(serializers.Serializer):
    filter_spec = HardwareSpecSerializer(required=False)
    frequency_low_passband = serializers.FloatField(required=False)
    frequency_high_passband = serializers.FloatField(required=False)
    frequency_low_stopband = serializers.FloatField(required=False)
    frequency_high_stopband = serializers.FloatField(required=False)


class RfPathSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    cal_source_id = serializers.CharField(required=True)
    filter_id = serializers.CharField(required=True)
    amplifier_id = serializers.CharField(required=True)


class PreselectorSerializer(serializers.Serializer):
    preselector_spec = HardwareSpecSerializer(required=False)
    cal_sources = CalSourceSerializer(many=True, required=False)
    amplifiers = AmplifierSerializer(many=True, required=False)
    filters = FilterSerializer(many=True, required=False)
    rf_paths = RfPathSerializer(many=True, required=False)


class SignalAnalyzerSerializer(serializers.Serializer):
    sigan_spec = HardwareSpecSerializer(required=False)
    frequency_low = serializers.FloatField(required=False)
    frequency_high = serializers.FloatField(required=False)
    noise_figure = serializers.FloatField(required=False)
    max_power = serializers.FloatField(required=False)
    a2d_bits = serializers.IntegerField(required=False)


class SensorSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    sensor_spec = HardwareSpecSerializer(required=False)
    antenna = AntennaSerializer(required=False)
    preselector = PreselectorSerializer(required=False)
    signal_analyzer = SignalAnalyzerSerializer(required=False)
    computer_spec = HardwareSpecSerializer(required=False)
    mobile = serializers.BooleanField(required=False)
    environment = EnvironmentSerializer(required=False)
    sensor_sha512 = serializers.CharField(required=False)
