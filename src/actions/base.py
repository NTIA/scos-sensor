import numpy as np

class Action(object):
    """The action base class.

    To create an action, create a subclass of `Action` with a descriptive
    docstring and override the `__call__` method.

    The scheduler reports the 'success' or 'failure' of an action by the
    following convention:

      * If at any point or for any reason that `__call__` function raises an
        exception, the task is marked a 'failure' and `str(err)` is provided
        as a detail to the user, where `err` is the raised Exception object.

      * If the `__call__` function returns normally, the task was a 'success',
        and if the value returned to the scheduler is a string, it will be
        added to the task result's detail field.

    """

    def __init__(self, admin_only=False):
        self.admin_only = admin_only

    def __call__(self, schedule_entry_name, task_id):
        raise NotImplementedError("Implement action logic.")

    def get_frequencies(self, data, measurement_params):
        frequency_info = {}
        timestep = 1 / measurement_params.sample_rate
        frequencies = np.fft.fftfreq(data.size, timestep)
        frequencies = np.fft.fftshift(frequencies) + measurement_params.center_frequency
        return frequencies

    @property
    def summary(self):
        try:
            return self.description.splitlines()[0]
        except IndexError:
            return "Summary not provided."

    @property
    def description(self):
        return self.__doc__
