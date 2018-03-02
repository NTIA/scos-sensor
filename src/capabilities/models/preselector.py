from django.db import models


MAX_CHARFIELD_LEN = 255


class Preselector(models.Model):
    """Implements Preselector as defined in the SCOS transfer spec.

    https://github.com/NTIA/SCOS-Transfer-Spec#preselector-object

    `rf_paths` is provided automatically by the RFPath model.

    """
    pass
