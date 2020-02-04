from sigmf.validate import validate as sigmf_validate


def check_metadata_fields(
    acquisition, entry_name, schedule_entry, is_multirecording=False
):
    assert sigmf_validate(acquisition.metadata)
    assert "ntia-scos:action" in acquisition.metadata["global"]
    assert (
        acquisition.metadata["global"]["ntia-scos:action"]["name"]
        == schedule_entry["action"]
    )
    assert "ntia-scos:schedule" in acquisition.metadata["global"]
    assert acquisition.metadata["global"]["ntia-scos:schedule"]["name"] == entry_name
    assert "ntia-scos:task" in acquisition.metadata["global"]
    assert (
        acquisition.metadata["global"]["ntia-scos:task"]
        == acquisition.task_result.task_id
    )
    if is_multirecording:
        assert "ntia-scos:recording" in acquisition.metadata["global"]
        assert (
            acquisition.metadata["global"]["ntia-scos:recording"]
            == acquisition.recording_id
        )
    else:
        assert "ntia-scos:recording" not in acquisition.metadata["global"]

    assert "ntia-core:measurement" in acquisition.metadata["global"]
    assert acquisition.metadata["global"]["ntia-core:measurement"]["time_start"]
    assert acquisition.metadata["global"]["ntia-core:measurement"]["time_stop"]
    assert acquisition.metadata["global"]["ntia-core:measurement"][
        "frequency_tuned_low"
    ]
    assert acquisition.metadata["global"]["ntia-core:measurement"][
        "frequency_tuned_high"
    ]
    assert acquisition.metadata["global"]["ntia-core:measurement"]["domain"]
    assert acquisition.metadata["global"]["ntia-core:measurement"]["measurement_type"]
