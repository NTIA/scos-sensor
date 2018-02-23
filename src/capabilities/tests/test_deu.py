from capabilities.models import DataExtractionUnit


def test_antenna_str():
    str(DataExtractionUnit(model="test_deu"))
