EMPTY_ACQUISITIONS_RESPONSE = []

SINGLE_ACQUISITION = {
    'name': 'test_acq',
    'start': None,
    'stop': None,
    'interval': None,
    'action': 'mock_acquire'
}

MULTIPLE_ACQUISITIONS = {
    'name': 'test_multiple_acq',
    'start': None,
    'stop': 5,
    'stop_is_relative': True,
    'interval': 1,
    'action': 'mock_acquire'
}
