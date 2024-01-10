from utils.component_registrar import gps_monitor
from scos_actions.hardware.mocks.mock_gps import MockGPS
from scos_actions.signals import register_gps


def test_gps_registration():
    mock_gps = MockGPS()
    register_gps.send(mock_gps, gps=mock_gps)
    assert gps_monitor.gps == mock_gps
