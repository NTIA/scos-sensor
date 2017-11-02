import numpy as np

from actions import usrp


uhd_is_available = True
is_available = True
radio = None


def connect(usrp_serial):
    return True


class RadioInterfaceMock(usrp.RadioInterface):
    def __init__(self, serial):
        self.radio = object()

    def finite_acquisition(n):
        return np.ones(n)
