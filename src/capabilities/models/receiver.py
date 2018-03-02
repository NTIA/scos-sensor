from django.db import models


MAX_CHARFIELD_LEN = 255


class DataExtractionUnit(models.Model):
    """Implements DataExtractionUnit as defined in the SCOS transfer spec.

    https://github.com/NTIA/SCOS-Transfer-Spec#dataextractionunit-object

    """
    model = models.CharField(
        max_length=MAX_CHARFIELD_LEN,
        help_text="Make and model of DEU. E.g., 'Ettus B200'.",
    )
    low_frequency = models.FloatField(
        help_text="Low frequency of operational range. [Hz]",
        blank=True,
        null=True,
    )
    high_frequency = models.FloatField(
        help_text="High frequency of operational range. [Hz]",
        blank=True,
        null=True,
    )
    noise_figure = models.FloatField(
        help_text="Noise Figure. [dB]",
        blank=True,
        null=True,
    )
    max_power = models.FloatField(
        help_text="Maximum input power. [dB]",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.model
