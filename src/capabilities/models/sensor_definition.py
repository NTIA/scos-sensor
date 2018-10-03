from django.db import models

MAX_CHARFIELD_LEN = 1024


class SensorDefinition(models.Model):
    """Implements SensorDefinition as defined in the SCOS transfer spec.

    https://github.com/NTIA/SCOS-Transfer-Spec#411-sensordefinition-object

    """
    host_controller = models.CharField(
        max_length=MAX_CHARFIELD_LEN,
        help_text=("Description of host computer. E.g. Make, model, "
                   "and configuration."),
        null=True,
        blank=True,
    )
    antenna = models.ForeignKey(
        'capabilities.Antenna',
        on_delete=models.PROTECT,
    )
    preselector = models.ForeignKey(
        'capabilities.Preselector',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    receiver = models.ForeignKey(
        'capabilities.Receiver',
        on_delete=models.PROTECT,
    )
