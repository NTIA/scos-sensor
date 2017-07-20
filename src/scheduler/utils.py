import time


def timefn() -> int:
    """Return a Unix timestamp with 1-second resolution."""
    return int(time.time())


delayfn = time.sleep
