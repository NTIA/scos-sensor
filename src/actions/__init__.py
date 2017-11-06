from . import acquire_single_freq_fft
from . import logger


by_name = {
    "acquire700c": acquire_single_freq_fft.SingleFrequencyFftAcquisition(
        frequency=751e6,
        sample_rate=15.36e6,
        fft_size=1024,
        nffts=300
    ),
    "logger": logger.Logger()
}


def get_action_with_summary(action):
    action_fn = by_name[action]
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


def init():
    """Allows re-initing VALID_ACTIONS if `by_name` is modified."""
    global VALID_ACTIONS
    global CHOICES

    VALID_ACTIONS = sorted(by_name.keys())
    for action in VALID_ACTIONS:
        CHOICES.append((action, get_action_with_summary(action)))


init()
