from __future__ import absolute_import

from django.db import models


MAX_CHARFIELD_LEN = 255


class SignalConditioningUnit(models.Model):
    """Implements SignalConditioningUnit as defined in the SCOS transfer spec.

    https://github.com/NTIA/SCOS-Transfer-Spec#signalconditioningunit-object

    `rf_path_spec` is provided automatically by the RFPath model.

    """
    pass
