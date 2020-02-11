from sensor import settings
from hardware.usrp_radio import USRPRadio

usrp_radio = None
keysight_n6841a_radio = None
radio = None


def get_radio():
    global usrp_radio

    if settings.SENSOR_TYPE == "USRP":
        if not usrp_radio:
            usrp_radio = USRPRadio()
        return usrp_radio
    # elif settings.SENSOR_TYPE == "KEYSIGHT_N6841A":
    #     if not keysight_n6841a_radio:
    #         keysight_n6841a_radio = KeysightN6841ARadio()
    #     return keysight_n6841a_radio
    else:
        raise Exception("Unsupported SENSOR_TYPE")


radio = get_radio()
