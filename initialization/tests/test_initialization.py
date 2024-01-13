from initialization import load_preselector

def test_load_preselector():
    preselector = load_preselector(
        {"name": "test", "base_url": "http://127.0.0.1"},
        "its_preselector.web_relay_preselector",
        "WebRelayPreselector",
    )
    assert preselector is not None