from rest_framework import serializers


class PreselectorStatusSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    healthy = serializers.BooleanField(required=True)
    noise_diode_powered = serializers.BooleanField(required=False)
    lna_powered = serializers.BooleanField(required=False)
    antenna_path_enabled = serializers.BooleanField(required=False)
    noise_diode_powered = serializers.BooleanField(required=False)


class SignalAnalyzerStatusSerializer(serializers.Serializer):
    model = serializers.CharField(required=True)
    healthy = serializers.BooleanField(required=True)


class SwitchStatusSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    healthy = serializers.BooleanField(required=True)
    rf_tray_powered = serializers.BooleanField(required=False)
    preselector_powered = serializers.BooleanField(required=False)
    _28v_aux_powered = serializers.BooleanField(required=False)
    sigan_powered = serializers.BooleanField(required=False)
    computer_powered = serializers.BooleanField(required=False)

    def get_fields(self):
        fields = super().get_fields()
        _28v_aux_powered = fields.pop("_28v_aux_powered")
        fields["28v_aux_powered"] = _28v_aux_powered
        return fields
