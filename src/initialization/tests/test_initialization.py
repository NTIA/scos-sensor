from src.initialization import load_preselector


def test_load_preselector():
    preselector = load_preselector(preselector_config=
        {"name": "test", "base_url": "http://127.0.0.1"},
        module="its_preselector.web_relay_preselector",
        preselector_class_name = "WebRelayPreselector", sensor_definition={}
    )
    assert preselector is not None