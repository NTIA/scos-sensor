from sigmf.validate import validate as sigmf_validate


def check_metadata_fields(acquisition, entry_name, schedule_entry, is_multirecording=False):
    assert sigmf_validate(acquisition.metadata)
    assert 'ntia-scos:action' in acquisition.metadata['global']
    assert acquisition.metadata['global']['ntia-scos:action']['name'] == schedule_entry['action']
    assert 'ntia-scos:schedule' in acquisition.metadata['global']
    assert acquisition.metadata['global']['ntia-scos:schedule']['name'] == entry_name
    assert acquisition.metadata['global']['ntia-scos:schedule']['action'] == schedule_entry['action']
    assert 'ntia-scos:task_id' in acquisition.metadata['global']
    assert acquisition.metadata['global']['ntia-scos:task_id'] == acquisition.task_result.task_id
    if is_multirecording:
        assert 'ntia-scos:recording_id' in acquisition.metadata['global']
        assert acquisition.metadata['global']['ntia-scos:recording_id'] == acquisition.recording_id
    else:
        assert 'ntia-scos:recording_id' not in acquisition.metadata['global']