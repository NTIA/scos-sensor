from . import acquire_single_freq_fft
from . import acquire_stepped_freq_tdomain_iq
from . import logger
from . import monitor_usrp
from . import sync_gps


# Actions initialized here are made available through the API
registered_actions = {
    "logger":
    logger.Logger(),
    "admin_logger":
    logger.Logger(loglvl=logger.LOGLVL_ERROR, admin_only=True),
    "monitor_usrp":
    monitor_usrp.UsrpMonitor(admin_only=True),
    "sync_gps":
    sync_gps.SyncGps(admin_only=True)
}

single_freq_ffts = [
    {
        "name": "acquire_700c_dl",
        "frequency": 751e6,
        "sample_rate": 15.36e6,
        "gain": 40,
        "fft_size": 1024,
        "nffts": 300
    },
    # Add more single-frequency FFT acquisitions here
    # {
    #     "name": "acquire_aws1_dl",
    #     "frequency": 2132.5e6,
    #     "sample_rate": 15.36e6,
    #     "gain": 40,
    #     "fft_size": 1024,
    #     "nffts": 300
    # },
]
for acq in single_freq_ffts:
    registered_actions[acq['name']] = \
        acquire_single_freq_fft.SingleFrequencyFftAcquisition(**acq)


stepped_freq_tdomain_iq = [
    {
        "name": "acquire_700_band_iq",
        "fcs": [707e6, 722e6, 737e6, 757e6, 772e6, 791e6],
        "gain": 40,
        "sample_rate": 22e6,
        "duration_ms": 30,
    },
    # Add more stepped frequency time domain IQ acquisitions here
]
for acq in stepped_freq_tdomain_iq:
    registered_actions[acq['name']] = \
        acquire_stepped_freq_tdomain_iq.SteppedFrequencyTimeDomainIq(**acq)


by_name = registered_actions


def get_action_with_summary(action):
    """Given an action, return the string 'action_name - summary'."""
    action_fn = registered_actions[action]
    summary = get_summary(action_fn)
    action_with_summary = action
    if summary:
        action_with_summary += " - {}".format(summary)

    return action_with_summary


def get_summary(action_fn):
    """Extract the first line of the action's description as a summary."""
    description = action_fn.description
    summary = None
    if description:
        summary = description.splitlines()[0]

    return summary


MAX_LENGTH = 50
VALID_ACTIONS = []
CHOICES = []
ADMIN_CHOICES = []


def init():
    """Allows re-initing VALID_ACTIONS if `registered_actions` is modified."""
    global VALID_ACTIONS
    global CHOICES

    VALID_ACTIONS = sorted(registered_actions.keys())
    for action in VALID_ACTIONS:
        if registered_actions[action].admin_only:
            ADMIN_CHOICES.append((action, get_action_with_summary(action)))
        else:
            CHOICES.append((action, get_action_with_summary(action)))


init()
