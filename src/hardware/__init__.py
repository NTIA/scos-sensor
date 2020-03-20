from sensor import settings
# from hardware.usrp_radio import USRPRadio

radio = None


def get_radio():
    global radio

    if settings.SENSOR_TYPE == "USRP":
        if not radio:
            radio = USRPRadio()
    else:
        raise Exception("Unsupported SENSOR_TYPE")


# get_radio()
