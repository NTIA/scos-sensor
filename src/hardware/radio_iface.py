from abc import ABC, abstractmethod


class RadioInterface(ABC):
    @property
    @abstractmethod
    def is_available(self):
        pass

    @property
    @abstractmethod
    def sample_rate(self):  # -> float:
        pass

    @sample_rate.setter
    @abstractmethod
    def sample_rate(self, sample_rate):
        pass

    @property
    @abstractmethod
    def frequency(self):  # -> float:
        pass

    @frequency.setter
    @abstractmethod
    def frequency(self, frequency):
        pass

    @abstractmethod
    def configure(self, action_name):
        pass

    @property
    @abstractmethod
    def gain(self):  # -> float:
        raise NotImplementedError("Implement gain getter")

    @gain.setter
    @abstractmethod
    def gain(self, gain):
        raise NotImplementedError("Implement gain setter")

    @abstractmethod
    def acquire_time_domain_samples(self, n, nskip=0, retries=5, subdev="A:A"):
        raise NotImplementedError("Implement acquire_time_domain_samples")

    @abstractmethod
    def create_calibration_annotation(self):
        pass
