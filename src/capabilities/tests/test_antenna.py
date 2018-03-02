from capabilities.models import Antenna


def test_antenna_str():
    str(Antenna(model="test_antenna"))
