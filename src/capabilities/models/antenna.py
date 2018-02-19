from django.contrib.postgres.fields import ArrayField
from django.db import models


MAX_CHARFIELD_LEN = 255


class Antenna(models.Model):
    """Implements Antenna as defined in the SCOS transfer spec.

    https://github.com/NTIA/SCOS-Transfer-Spec#antenna-object

    """
    model = models.CharField(
        max_length=MAX_CHARFIELD_LEN,
        help_text="Antenna make and model number. E.g. 'ARA CSB-16'.",
    )
    type = models.CharField(
        max_length=MAX_CHARFIELD_LEN,
        help_text="Antenna type. E.g. 'dipole'.",
        blank=True,
        null=True,
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
    gain = models.FloatField(
        help_text=("Antenna gain in direction of "
                   "maximum radiation or reception. [dBi]"),
        blank=True,
        null=True,
    )
    horizontal_gain_pattern = ArrayField(
        models.FloatField(),
        help_text="Antenna gain pattern in horizontal plane. [dBi]",
        blank=True,
    )
    vertical_gain_pattern = ArrayField(
        models.FloatField(),
        help_text="Antenna gain pattern in vertical plane. [dBi]",
        blank=True,
    )
    horizontal_beam_width = models.FloatField(
        help_text="Horizontal 3-dB beamwidth. [degrees]",
        blank=True,
        null=True,
    )
    vertical_beam_width = models.FloatField(
        help_text="Vertical 3-dB beamwidth. [degrees]",
        blank=True,
        null=True,
    )
    cross_polar_discrimintation = models.FloatField(
        help_text="Cross-polarization discrimination.",
        blank=True,
        null=True,
    )
    voltage_standing_wave_ratio = models.FloatField(
        help_text="Voltage standing wave ratio. [volts]",
        blank=True,
        null=True,
    )
    cable_loss = models.FloatField(
        help_text="Loss for cable connecting antenna and preselector. [dB]",
        blank=True,
        null=True,
    )
    steerable = models.NullBooleanField(
        help_text="Defines if the antenna is steerable or not.",
        blank=True,
        null=True,
    )
    mobile = models.NullBooleanField(
        help_text="Defines if the antenna is mobile or not.",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.model
