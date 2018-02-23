from capabilities.models import RFPath, SignalConditioningUnit


def test_antenna_str():
    scu = SignalConditioningUnit()
    str(RFPath(signal_condition_unit=scu))
    str(RFPath(signal_condition_unit=scu, rf_path_number=1))
