EMPTY_SCHEDULE_REPONSE = []

TEST_SCHEDULE_ENTRY = {
    'name': 'test',
    'action': 'logger',
    'is_private': False
}

TEST_ALTERNATE_SCHEDULE_ENTRY = {
    'name': 'test_alternate',
    'action': 'logger',
    'is_private': False,
    'priority': 5
}

TEST_PRIVATE_SCHEDULE_ENTRY = {
    'name': 'test_private',
    'action': 'logger',
    'is_private': True
}

TEST_NONSENSE_SCHEDULE_ENTRY = {
    'name': 'test_nonsense',
    'action': 'logger',
    'nonsense': True
}
