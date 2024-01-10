from scos_actions.hardware.mocks.mock_sigan import MockSignalAnalyzer
from scos_actions.signals import register_signal_analyzer

from utils.component_registrar import sigan_monitor


def test_sigan_registration():
    sigan = MockSignalAnalyzer()
    register_signal_analyzer.send(__name__, signal_analyzer=sigan)
    assert sigan_monitor.signal_analyzer == sigan
