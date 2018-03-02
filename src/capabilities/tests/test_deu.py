from capabilities.models import Receiver


def test_antenna_str():
    str(Receiver(model="test_receiver"))
