from status.utils import get_location

GLOBAL_INFO = {
    "core:version": "0.0.2",
    "core:extensions": {
        "ntia-algorithm": "v1.0.0",
        "ntia-core": "v1.0.0",
        "ntia-environment": "v1.0.0",
        "ntia-location": "v1.0.0",
        "ntia-scos": "v1.0.0",
        "ntia-sensor": "v1.0.0",
    },
}


def get_coordinate_system_sigmf():
    return {
        "id": "WGS 1984",
        "coordinate_system_type": "GeographicCoordinateSystem",
        "distance_unit": "decimal degrees",
        "time_unit": "seconds",
    }


def get_sensor_location_sigmf(sensor):
    database_location = get_location()
    if database_location:
        if "location" not in sensor:
            sensor["location"] = {}
        if "x" not in sensor["location"] or not sensor["location"]["x"]:
            sensor["location"]["x"] = database_location.longitude
        if "y" not in sensor["location"] or not sensor["location"]["y"]:
            sensor["location"]["y"] = database_location.latitude
