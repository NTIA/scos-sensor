# Defines capabilities that are displayed verbatim on /capabilities.
#
# Each capability must be JSON serializable, meaning a string, number (float or
# integer), list, or dictionary of the above.
#
# Imports and helper artifacts are permitted but should be removed from the
# global namespace (using `del`) in the cleanup section at the bottom of the
# file.

# setup - imports and helpers

# capabilities
# ------------

# TODO: these are stubs
minimum_frequency = 400e6
maximum_frequency = 6e7
mobility = False

# ------------
# capabilities

# cleanup - delete imports and artifacts that are not "capabilities"

assert 'actions' not in globals(), (
    "Actions are added automatically by the capabilities serializer. "
    "Do not define them explicitely in capabilities.py.")
