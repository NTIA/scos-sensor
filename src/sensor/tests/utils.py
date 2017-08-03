from rest_framework import status


def validate_response(response, expected_code=None):
    actual_code = response.status_code
    if expected_code is None:
        assert status.is_success(actual_code)
    else:
        assert actual_code == expected_code, response.context

    if actual_code not in (status.HTTP_204_NO_CONTENT,):
        rjson = response.json()
        return rjson
