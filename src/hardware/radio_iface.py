from abc import ABC
from sensor import settings
from usrp_iface import USRPRadio


def get_radio():
    if settings.SENSOR_TYPE == "USRP":
        return USRPRadio()
    elif settings.SENSOR_TYPE == "KEYSIGHT":
        return KeysightRadio()
    elif settings.SENSOR_TYPE == "MOCK":
        return MockRadio()
    elif settings.SENSOR_TYPE == "MOCK_RANDOM" or settings.SENSOR_TYPE == "MOCK_RANDOM_32":
        return MockRadio(random=True)
    else:
        raise Exception("Unsupported SENSOR_TYPE")

class RadioInterface(ABC):

    @property
    @abstractmethod
    def sample_rate(self):  # -> float:
        raise NotImplementedError("Implement sample_rate getter")

    @sample_rate.setter
    @abstractmethod
    def sample_rate(self, sample_rate):
        raise NotImplementedError("Implement sample_rate setter")

    @property
    @abstractmethod
    def frequency(self):  # -> float:
        raise NotImplementedError("Implement frequency getter")

    @frequency.setter
    @abstractmethod
    def frequency(self, frequency):
        raise NotImplementedError("Implement frequency setter")

    @property
    @abstractmethod
    def gain(self):  # -> float:
        raise NotImplementedError("Implement gain getter")

    @gain.setter
    @abstractmethod
    def gain(self, gain):
        raise NotImplementedError("Implement gain setter")

    @abstractmethod
    def acquire_time_domain_samples(self, n, nskip=0, retries=5):
        raise NotImplementedError("Implement acquire_time_domain_samples")

    @abstractmethod
    def acquire_frequency_domain_samples(self, fft_size, num_ffts, retries=5):
        raise NotImplementedError("Implement acquire_frequency_domain_samples")

    @abstractmethod
    def create_calibration_annotation(self):
        raise NotImplementedError("Implement create_calibration_annotation")