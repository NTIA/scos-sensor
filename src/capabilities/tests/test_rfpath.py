from capabilities.models import RFPath, Preselector


def test_antenna_str():
    ps = Preselector()
    str(RFPath(preselector=ps))
    str(RFPath(preselector=ps, rf_path_number=1))
