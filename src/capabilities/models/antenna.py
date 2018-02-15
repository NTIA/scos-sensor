from django.contrib.postgres.fields import ArrayField
from django.db import models


MAX_CHARFIELD_LEN = 255


class Antenna(models.Model):
    """Defines the Antenna object defined in the SCOS transfer spec.

    https://github.com/NTIA/SCOS-Transfer-Spec#antenna-object

    """
    model = models.CharField(
        max_length=MAX_CHARFIELD_LEN,
        help_text="Antenna make and model number. E.g. 'ARA CSB-16'."
    )
    type = models.CharField(
        max_length=MAX_CHARFIELD_LEN,
        help_text="Antenna type. E.g. 'dipole'.",
        null=True,
    )
    low_frequency = models.FloatField(
        help_text="Low frequency of operational range. [Hz]",
        null=True,
    )
    high_frequency = models.FloatField(
        help_text="High frequency of operational range. [Hz]",
        null=True,
    )
    gain = models.FloatField(
        help_text=("Antenna gain in direction of "
                   "maximum radiation or reception. [dBi]"),
        null=True,
    )
    horizontal_gain_pattern = ArrayField(
        models.FloatField(),
        blank=True,
        help_text="Antenna gain pattern in horizontal plane. [dBi]"
    )
    vertical_gain_pattern = ArrayField(
        models.FloatField(),
        blank=True,
        help_text="Antenna gain pattern in vertical plane. [dBi]"
    )
    horizontal_beam_width = models.FloatField(
        help_text="Horizontal 3-dB beamwidth. [degrees]",
        null=True,
    )
    vertical_beam_width = models.FloatField(
        help_text="Vertical 3-dB beamwidth. [degrees]",
        null=True,
    )
    cross_polar_discrimintation = models.FloatField(
        help_text="Cross-polarization discrimination.",
        null=True,
    )
    voltage_standing_wave_ratio = models.FloatField(
        help_text="Voltage standing wave ratio. [volts]",
        null=True,
    )
    cable_loss = models.FloatField(
        help_text="Loss for cable connecting antenna and preselector. [dB]",
        null=True,
    )
    steerable = models.BooleanField(
        help_text="Defines if the antenna is steerable or not.",
        null=True,
    )
    mobile = models.BooleanField(
        help_text="Defines if the antenna is mobile or not.",
        null=True,
    )
