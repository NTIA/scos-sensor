from django.db import models


MAX_CHARFIELD_LEN = 255


class RFPath(models.Model):
    """Implements RFPath as defined in the SCOS transfer spec.

    https://github.com/NTIA/SCOS-Transfer-Spec#rfpath-object

    """
    signal_condition_unit = models.ForeignKey(
        'capabilities.SignalConditioningUnit',
        on_delete=models.CASCADE,
        related_name='rf_path_spec',
    )
    rf_path_number = models.PositiveSmallIntegerField(
        help_text="RF path number.",
        blank=True,
        null=True,
    )
    low_frequency_passband = models.FloatField(
        help_text="Low frequency of filter 1-dB passband. [Hz]",
        blank=True,
        null=True,
    )
    high_frequency_passband = models.FloatField(
        help_text="High frequency of filter 1-dB passband. [Hz]",
        blank=True,
        null=True,
    )
    low_frequency_stopband = models.FloatField(
        help_text="Low frequency of filter 1-dB stopband. [Hz]",
        blank=True,
        null=True,
    )
    high_frequency_stopband = models.FloatField(
        help_text="High frequency of filter 1-dB stopband. [Hz]",
        blank=True,
        null=True,
    )
    lna_gain = models.FloatField(
        help_text="Gain of low noise amplifier. [dB]",
        blank=True,
        null=True,
    )
    lna_noise_figure = models.FloatField(
        help_text="Noise figure of low noise amplifier. [dB]",
        blank=True,
        null=True,
    )
    cal_source_type = models.CharField(
        max_length=MAX_CHARFIELD_LEN,
        help_text="E.g., 'calibrated noise source'.",
        blank=True,
        null=True,
    )
    cal_source_enr = models.FloatField(
        help_text=("Excess noise ratio of calibrated noise source at "
                   "frequency of RF path. [dB]"),
        blank=True,
        null=True
    )

    class Meta:
        ordering = ('rf_path_number',)

    def __str__(self):
        path_number = ""
        if self.rf_path_number:
            return "RF Path {}".format(path_number)

        return "RF Path"
