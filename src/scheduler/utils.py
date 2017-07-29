import time


def timefn():
    """Return a Unix timestamp with 1-second resolution."""
    return int(time.time())


delayfn = time.sleep
